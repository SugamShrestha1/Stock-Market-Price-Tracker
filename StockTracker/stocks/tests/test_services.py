from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase, override_settings

from StockTracker.stocks.services import get_current_price, get_historical_prices


class GetHistoricalPricesTests(TestCase):
    @staticmethod
    def build_response(payload):
        response = MagicMock()
        response.raise_for_status.return_value = None
        response.json.return_value = payload
        return response

    @staticmethod
    def build_time_series():
        return {
            "2024-01-01": {
                "1. open": "100.00",
                "2. high": "110.00",
                "3. low": "95.00",
                "4. close": "105.00",
                "5. volume": "1000",
            },
            "2024-01-02": {
                "1. open": "105.00",
                "2. high": "115.00",
                "3. low": "100.00",
                "4. close": "110.00",
                "5. volume": "2000",
            },
            "2024-01-03": {
                "1. open": "110.00",
                "2. high": "120.00",
                "3. low": "105.00",
                "4. close": "115.00",
                "5. volume": "3000",
            },
            "2024-01-04": {
                "1. open": "115.00",
                "2. high": "125.00",
                "3. low": "110.00",
                "4. close": "120.00",
                "5. volume": "4000",
            },
        }

    @override_settings(ALPHA_VANTAGE_API_KEY="demo-key")
    @patch("StockTracker.stocks.services.requests.get")
    def test_get_historical_prices_successfully_parses_and_filters_records(self, mock_get):
        payload = {"Time Series (Daily)": self.build_time_series()}
        mock_get.return_value = self.build_response(payload)

        from_timestamp = int(datetime(2024, 1, 2, tzinfo=timezone.utc).timestamp())
        to_timestamp = int(datetime(2024, 1, 3, tzinfo=timezone.utc).timestamp())

        result = get_historical_prices("aapl", "D", from_timestamp, to_timestamp)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["timestamp"], from_timestamp)
        self.assertEqual(result[0]["close_price"], 110.0)
        self.assertEqual(result[1]["timestamp"], to_timestamp)
        self.assertEqual(result[1]["volume"], 3000)

    @override_settings(ALPHA_VANTAGE_API_KEY="demo-key")
    @patch("StockTracker.stocks.services.requests.get")
    def test_get_historical_prices_converts_symbol_to_uppercase_and_verifies_request_details(self, mock_get):
        payload = {"Time Series (Daily)": {"2024-01-02": {
            "1. open": "105.00",
            "2. high": "115.00",
            "3. low": "100.00",
            "4. close": "110.00",
            "5. volume": "2000",
        }}}
        mock_get.return_value = self.build_response(payload)

        get_historical_prices("aapl", "D", 0, 9999999999)

        mock_get.assert_called_once()
        self.assertEqual(mock_get.call_args.args[0], "https://www.alphavantage.co/query")
        self.assertEqual(mock_get.call_args.kwargs["timeout"], 10)
        self.assertEqual(mock_get.call_args.kwargs["params"]["function"], "TIME_SERIES_DAILY")
        self.assertEqual(mock_get.call_args.kwargs["params"]["symbol"], "AAPL")
        self.assertEqual(mock_get.call_args.kwargs["params"]["outputsize"], "compact")
        self.assertEqual(mock_get.call_args.kwargs["params"]["apikey"], "demo-key")

    @override_settings(ALPHA_VANTAGE_API_KEY="demo-key")
    @patch("StockTracker.stocks.services.requests.get")
    def test_get_historical_prices_converts_dates_to_unix_timestamps(self, mock_get):
        payload = {"Time Series (Daily)": {
            "2024-01-02": {
                "1. open": "105.00",
                "2. high": "115.00",
                "3. low": "100.00",
                "4. close": "110.00",
                "5. volume": "2000",
            }
        }}
        mock_get.return_value = self.build_response(payload)

        result = get_historical_prices("aapl", "D", 1704153600, 1704153600)

        self.assertEqual(result[0]["timestamp"], 1704153600)

    @override_settings(ALPHA_VANTAGE_API_KEY="demo-key")
    @patch("StockTracker.stocks.services.requests.get")
    def test_get_historical_prices_rejects_unsupported_resolutions(self, mock_get):
        with self.assertRaisesMessage(ValueError, "Unsupported resolution. Only daily resolution 'D' is supported."):
            get_historical_prices("aapl", "W", 0, 9999999999)

        mock_get.assert_not_called()

    @override_settings(ALPHA_VANTAGE_API_KEY="")
    @patch("StockTracker.stocks.services.requests.get")
    def test_get_historical_prices_raises_if_api_key_is_missing(self, mock_get):
        with self.assertRaisesMessage(ValueError, "Alpha Vantage API key is not configured."):
            get_historical_prices("aapl", "D", 0, 9999999999)

        mock_get.assert_not_called()

    @override_settings(ALPHA_VANTAGE_API_KEY="demo-key")
    @patch("StockTracker.stocks.services.requests.get")
    def test_get_historical_prices_handles_alpha_vantage_error_message(self, mock_get):
        mock_get.return_value = self.build_response({"Error Message": "Something went wrong."})

        with self.assertRaisesMessage(ValueError, "Alpha Vantage returned an error for the requested symbol."):
            get_historical_prices("aapl", "D", 0, 9999999999)

    @override_settings(ALPHA_VANTAGE_API_KEY="demo-key")
    @patch("StockTracker.stocks.services.requests.get")
    def test_get_historical_prices_handles_alpha_vantage_note_response(self, mock_get):
        mock_get.return_value = self.build_response({"Note": "API rate limit reached."})

        with self.assertRaisesMessage(ValueError, "Alpha Vantage API limit reached. Please try again later."):
            get_historical_prices("aapl", "D", 0, 9999999999)

    @override_settings(ALPHA_VANTAGE_API_KEY="demo-key")
    @patch("StockTracker.stocks.services.requests.get")
    def test_get_historical_prices_handles_alpha_vantage_information_response(self, mock_get):
        mock_get.return_value = self.build_response({"Information": "The API is temporarily unavailable."})

        with self.assertRaisesMessage(ValueError, "Alpha Vantage returned an informational message; please try again later."):
            get_historical_prices("aapl", "D", 0, 9999999999)

    @override_settings(ALPHA_VANTAGE_API_KEY="demo-key")
    @patch("StockTracker.stocks.services.requests.get")
    def test_get_historical_prices_handles_missing_or_invalid_time_series_data(self, mock_get):
        mock_get.return_value = self.build_response({"Time Series (Daily)": {}})

        with self.assertRaisesMessage(ValueError, "No historical data available for AAPL."):
            get_historical_prices("aapl", "D", 0, 9999999999)

        mock_get.return_value = self.build_response({"Time Series (Daily)": "invalid"})

        with self.assertRaisesMessage(ValueError, "No historical data available for AAPL."):
            get_historical_prices("aapl", "D", 0, 9999999999)

    @override_settings(ALPHA_VANTAGE_API_KEY="demo-key")
    @patch("StockTracker.stocks.services.requests.get")
    def test_get_historical_prices_skips_records_with_invalid_ohlcv_values(self, mock_get):
        payload = {"Time Series (Daily)": {
            "2024-01-01": {
                "1. open": "100.00",
                "2. high": "110.00",
                "3. low": "95.00",
                "4. close": "105.00",
                "5. volume": "1000",
            },
            "2024-01-02": {
                "1. open": "invalid",
                "2. high": "115.00",
                "3. low": "100.00",
                "4. close": "110.00",
                "5. volume": "2000",
            },
            "2024-01-03": {
                "1. open": "110.00",
                "2. high": "120.00",
                "3. low": "105.00",
                "4. close": "115.00",
                "5. volume": "3000",
            },
        }}
        mock_get.return_value = self.build_response(payload)

        result = get_historical_prices("aapl", "D", 0, 9999999999)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["timestamp"], int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp()))
        self.assertEqual(result[1]["timestamp"], int(datetime(2024, 1, 3, tzinfo=timezone.utc).timestamp()))

    @override_settings(ALPHA_VANTAGE_API_KEY="demo-key")
    @patch("StockTracker.stocks.services.requests.get")
    def test_get_historical_prices_raises_when_no_records_match_date_range(self, mock_get):
        payload = {"Time Series (Daily)": self.build_time_series()}
        mock_get.return_value = self.build_response(payload)

        from_timestamp = int(datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp())
        to_timestamp = int(datetime(2025, 1, 2, tzinfo=timezone.utc).timestamp())

        with self.assertRaisesMessage(ValueError, "No historical data available for AAPL in the requested date range."):
            get_historical_prices("aapl", "D", from_timestamp, to_timestamp)

    @override_settings(ALPHA_VANTAGE_API_KEY="demo-key")
    @patch("StockTracker.stocks.services.requests.get")
    def test_get_historical_prices_returns_records_in_ascending_chronological_order(self, mock_get):
        payload = {"Time Series (Daily)": {
            "2024-01-04": {
                "1. open": "115.00",
                "2. high": "125.00",
                "3. low": "110.00",
                "4. close": "120.00",
                "5. volume": "4000",
            },
            "2024-01-02": {
                "1. open": "105.00",
                "2. high": "115.00",
                "3. low": "100.00",
                "4. close": "110.00",
                "5. volume": "2000",
            },
            "2024-01-03": {
                "1. open": "110.00",
                "2. high": "120.00",
                "3. low": "105.00",
                "4. close": "115.00",
                "5. volume": "3000",
            },
        }}
        mock_get.return_value = self.build_response(payload)

        result = get_historical_prices("aapl", "D", 0, 9999999999)

        timestamps = [item["timestamp"] for item in result]
        self.assertEqual(timestamps, sorted(timestamps))


class GetCurrentPriceTests(TestCase):
    @staticmethod
    def build_response(payload):
        response = MagicMock()
        response.raise_for_status.return_value = None
        response.json.return_value = payload
        return response

    @override_settings(FINNHUB_API_KEY="demo-key")
    @patch("StockTracker.stocks.services.requests.get")
    def test_get_current_price_successfully_retrieves_and_parses_data(self, mock_get):
        mock_get.return_value = self.build_response({
            "c": 345.67,
            "d": 4.32,
            "dp": 1.27,
            "h": 350.0,
            "l": 340.0,
            "o": 342.5,
            "pc": 341.35,
        })

        result = get_current_price("aapl")

        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["current_price"], 345.67)
        self.assertEqual(result["change"], 4.32)
        self.assertEqual(result["percentage_change"], 1.27)
        self.assertEqual(result["high"], 350.0)
        self.assertEqual(result["low"], 340.0)
        self.assertEqual(result["open"], 342.5)
        self.assertEqual(result["previous_close"], 341.35)

    @override_settings(FINNHUB_API_KEY="demo-key")
    @patch("StockTracker.stocks.services.requests.get")
    def test_get_current_price_converts_symbol_to_uppercase(self, mock_get):
        mock_get.return_value = self.build_response({
            "c": 123.45,
            "d": 1.0,
            "dp": 0.81,
            "h": 125.0,
            "l": 121.0,
            "o": 122.0,
            "pc": 122.0,
        })

        result = get_current_price("msft")

        self.assertEqual(result["symbol"], "MSFT")
        self.assertEqual(mock_get.call_args.kwargs["params"]["symbol"], "MSFT")

    @override_settings(FINNHUB_API_KEY="demo-key")
    @patch("StockTracker.stocks.services.requests.get")
    def test_get_current_price_sends_correct_url_params_and_headers(self, mock_get):
        mock_get.return_value = self.build_response({
            "c": 100.0,
            "d": 2.0,
            "dp": 2.0,
            "h": 110.0,
            "l": 90.0,
            "o": 98.0,
            "pc": 98.0,
        })

        get_current_price("AAPL")

        self.assertEqual(mock_get.call_args.args[0], "https://finnhub.io/api/v1/quote")
        self.assertEqual(mock_get.call_args.kwargs["params"]["symbol"], "AAPL")
        self.assertEqual(mock_get.call_args.kwargs["headers"]["X-Finnhub-Token"], "demo-key")
        self.assertEqual(mock_get.call_args.kwargs["timeout"], 10)

    @override_settings(FINNHUB_API_KEY="")
    @patch("StockTracker.stocks.services.requests.get")
    def test_get_current_price_raises_if_api_key_is_missing(self, mock_get):
        with self.assertRaisesMessage(ValueError, "Finnhub API key is not configured."):
            get_current_price("AAPL")

        mock_get.assert_not_called()

    @override_settings(FINNHUB_API_KEY="demo-key")
    @patch("StockTracker.stocks.services.requests.get")
    def test_get_current_price_raises_when_no_current_price_is_returned(self, mock_get):
        mock_get.return_value = self.build_response({
            "c": 0,
            "d": 0,
            "dp": 0,
            "h": 0,
            "l": 0,
            "o": 0,
            "pc": 0,
        })

        with self.assertRaisesMessage(ValueError, "No price data available for AAPL."):
            get_current_price("AAPL")

        mock_get.return_value = self.build_response({
            "d": 0,
            "dp": 0,
            "h": 0,
            "l": 0,
            "o": 0,
            "pc": 0,
        })

        with self.assertRaisesMessage(ValueError, "No price data available for AAPL."):
            get_current_price("AAPL")

    @override_settings(FINNHUB_API_KEY="demo-key")
    @patch("StockTracker.stocks.services.requests.get")
    def test_get_current_price_raises_for_http_error(self, mock_get):
        mock_get.side_effect = requests.HTTPError("Bad request from Finnhub")

        with self.assertRaises(requests.HTTPError):
            get_current_price("AAPL")

    @override_settings(FINNHUB_API_KEY="demo-key")
    @patch("StockTracker.stocks.services.requests.get")
    def test_get_current_price_handles_request_timeout(self, mock_get):
        mock_get.side_effect = requests.Timeout("Request timed out")

        with self.assertRaises(requests.Timeout):
            get_current_price("AAPL")

    @override_settings(FINNHUB_API_KEY="demo-key")
    @patch("StockTracker.stocks.services.requests.get")
    def test_get_current_price_handles_invalid_json_response(self, mock_get):
        mock_get.return_value = self.build_response({})
        mock_get.return_value.json.side_effect = ValueError("Malformed JSON")

        with self.assertRaises(ValueError):
            get_current_price("AAPL")
