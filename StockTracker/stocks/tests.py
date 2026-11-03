from unittest.mock import patch

from django.test import TestCase

from .models import Stock


class RootURLTests(TestCase):
    def test_root_url_returns_success(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertIn('StockTracker API', response.json()['message'])


class StockAPITests(TestCase):
    def setUp(self):
        self.apple = Stock.objects.create(
            symbol='AAPL',
            company_name='Apple Inc.',
            exchange='NASDAQ',
            sector='Technology',
            industry='Consumer Electronics',
            currency='USD',
        )
        self.msft = Stock.objects.create(
            symbol='MSFT',
            company_name='Microsoft Corporation',
            exchange='NASDAQ',
            sector='Technology',
            industry='Software - Infrastructure',
            currency='USD',
        )
        self.nke = Stock.objects.create(
            symbol='NKE',
            company_name='Nike Inc.',
            exchange='NYSE',
            sector='Consumer Cyclical',
            industry='Footwear & Accessories',
            currency='USD',
        )

    def test_get_all_stocks(self):
        response = self.client.get('/api/stocks/')

        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.json())
        self.assertGreaterEqual(response.json()['count'], 3)

    def test_get_one_stock(self):
        response = self.client.get(f'/api/stocks/{self.apple.pk}/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['symbol'], 'AAPL')

    def test_search_stocks(self):
        response = self.client.get('/api/stocks/?search=Apple')

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.json()['count'], 1)
        self.assertIn('Apple', response.json()['results'][0]['company_name'])

    def test_filter_stocks(self):
        response = self.client.get('/api/stocks/?exchange=NASDAQ&sector=Technology')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 2)

    def test_stock_pagination(self):
        for i in range(12):
            Stock.objects.create(
                symbol=f'TEST{i}',
                company_name=f'Test Company {i}',
                exchange='NASDAQ',
                sector='Technology',
                industry='Software',
                currency='USD',
            )

        response = self.client.get('/api/stocks/?page=1')

        self.assertEqual(response.status_code, 200)
        self.assertIn('next', response.json())
        self.assertEqual(len(response.json()['results']), 10)

    @patch('StockTracker.stocks.views.get_current_price')
    def test_get_stock_quote(self, mock_get_current_price):
        mock_get_current_price.return_value = {
            'symbol': 'AAPL',
            'current_price': 344.63,
            'change': -4.28,
            'percentage_change': -1.2267,
            'high': 349.19,
            'low': 334.35,
            'open': 346.715,
            'previous_close': 348.91,
        }

        response = self.client.get('/api/stocks/AAPL/quote/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['symbol'], 'AAPL')
        self.assertEqual(response.json()['current_price'], 344.63)


class HistoricalStockAPITests(TestCase):

    @patch('StockTracker.stocks.views.get_historical_prices')
    def test_get_historical_prices(self, mock_get_historical_prices):
        mock_get_historical_prices.return_value = [
            {
                'open_price': 250.00,
                'high_price': 255.00,
                'low_price': 248.00,
                'close_price': 253.00,
                'volume': 30000000,
                'timestamp': 1790899200,
            }
        ]

        response = self.client.get(
            '/api/stocks/AAPL/history/?resolution=D&from=1790860897&to=1793452897'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['close_price'], 253.00)

        mock_get_historical_prices.assert_called_once()

    def test_historical_prices_missing_from(self):
        response = self.client.get(
            '/api/stocks/AAPL/history/?resolution=D&to=1793452897'
        )

        self.assertEqual(response.status_code, 400)

    def test_historical_prices_missing_to(self):
        response = self.client.get(
            '/api/stocks/AAPL/history/?resolution=D&from=1790860897'
        )

        self.assertEqual(response.status_code, 400)

    def test_historical_prices_invalid_timestamp(self):
        response = self.client.get(
            '/api/stocks/AAPL/history/?resolution=D&from=invalid&to=1793452897'
        )

        self.assertEqual(response.status_code, 400)

    def test_historical_prices_invalid_date_range(self):
        response = self.client.get(
            '/api/stocks/AAPL/history/?resolution=D&from=1793452897&to=1790860897'
        )

        self.assertEqual(response.status_code, 400)

    @patch('StockTracker.stocks.views.get_historical_prices')
    def test_historical_prices_unsupported_resolution(self, mock_get_historical_prices):
        mock_get_historical_prices.side_effect = ValueError(
            "Unsupported resolution."
        )

        response = self.client.get(
            '/api/stocks/AAPL/history/?resolution=W&from=1790860897&to=1793452897'
        )

        self.assertEqual(response.status_code, 400)

    @patch('StockTracker.stocks.views.get_historical_prices')
    def test_historical_prices_external_api_failure(self, mock_get_historical_prices):
        import requests

        mock_get_historical_prices.side_effect = requests.RequestException(
            "External API unavailable."
        )

        response = self.client.get(
            '/api/stocks/AAPL/history/?resolution=D&from=1790860897&to=1793452897'
        )

        self.assertEqual(response.status_code, 502)
