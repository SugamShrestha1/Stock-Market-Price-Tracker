from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from StockTracker.accounts.models import User
from StockTracker.portfolio.models import PortfolioTransaction
from StockTracker.stocks.models import Stock


class PortfolioTransactionAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='alice',
            email='alice@example.com',
            password='password123',
        )
        self.other_user = User.objects.create_user(
            username='bob',
            email='bob@example.com',
            password='password123',
        )
        self.stock = Stock.objects.create(
            symbol='AAPL',
            company_name='Apple Inc.',
            exchange='NASDAQ',
            sector='Technology',
            industry='Consumer Electronics',
            currency='USD',
        )

    def test_get_returns_only_the_authenticated_users_transactions(self):
        PortfolioTransaction.objects.create(
            user=self.user,
            stock=self.stock,
            transaction_type='BUY',
            quantity=10,
            price='150.00',
        )
        PortfolioTransaction.objects.create(
            user=self.other_user,
            stock=self.stock,
            transaction_type='SELL',
            quantity=2,
            price='160.00',
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('portfolio:transactions'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['stock'], self.stock.id)
        self.assertEqual(response.data[0]['transaction_type'], 'BUY')

    def test_post_creates_transaction_for_authenticated_user(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            'stock': self.stock.id,
            'transaction_type': 'BUY',
            'quantity': 5,
            'price': '120.50',
            'transaction_date': '2026-11-03',
        }

        response = self.client.post(reverse('portfolio:transactions'), payload, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(PortfolioTransaction.objects.filter(user=self.user).count(), 1)
        self.assertEqual(response.data['stock'], self.stock.id)
        self.assertEqual(response.data['transaction_type'], 'BUY')
        self.assertEqual(response.data['quantity'], 5)


class PortfolioHoldingsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='alice',
            email='alice@example.com',
            password='password123',
        )
        self.other_user = User.objects.create_user(
            username='bob',
            email='bob@example.com',
            password='password123',
        )
        self.stock_a = Stock.objects.create(
            symbol='NABIL',
            company_name='Nabil Bank Limited',
            exchange='NEPSE',
            sector='Banking',
            industry='Banking',
            currency='NPR',
        )
        self.stock_b = Stock.objects.create(
            symbol='NLIC',
            company_name='Nepal Life Insurance',
            exchange='NEPSE',
            sector='Insurance',
            industry='Life Insurance',
            currency='NPR',
        )
        self.stock_c = Stock.objects.create(
            symbol='NICA',
            company_name='NIC Asia Bank',
            exchange='NEPSE',
            sector='Banking',
            industry='Banking',
            currency='NPR',
        )

    def test_get_holdings_uses_weighted_average_cost_for_multiple_buys_and_partial_sells(self):
        PortfolioTransaction.objects.create(user=self.user, stock=self.stock_a, transaction_type='BUY', quantity=10, price='500.00')
        PortfolioTransaction.objects.create(user=self.user, stock=self.stock_a, transaction_type='BUY', quantity=5, price='550.00')
        PortfolioTransaction.objects.create(user=self.user, stock=self.stock_a, transaction_type='SELL', quantity=3, price='600.00')

        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('portfolio:holdings'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['holdings'][0]['stock_id'], self.stock_a.id)
        self.assertEqual(response.data['holdings'][0]['total_bought'], 15)
        self.assertEqual(response.data['holdings'][0]['total_sold'], 3)
        self.assertEqual(response.data['holdings'][0]['quantity'], 12)
        self.assertEqual(response.data['holdings'][0]['average_purchase_price'], '516.67')

    def test_get_holdings_excludes_complete_sales_and_caps_sell_quantity_to_owned_shares(self):
        PortfolioTransaction.objects.create(user=self.user, stock=self.stock_a, transaction_type='BUY', quantity=8, price='100.00')
        PortfolioTransaction.objects.create(user=self.user, stock=self.stock_a, transaction_type='BUY', quantity=2, price='200.00')
        PortfolioTransaction.objects.create(user=self.user, stock=self.stock_a, transaction_type='SELL', quantity=15, price='220.00')

        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('portfolio:holdings'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['holdings'], [])

    def test_get_holdings_excludes_zero_holdings_and_handles_multiple_stocks(self):
        PortfolioTransaction.objects.create(user=self.user, stock=self.stock_a, transaction_type='BUY', quantity=5, price='100.00')
        PortfolioTransaction.objects.create(user=self.user, stock=self.stock_a, transaction_type='SELL', quantity=5, price='110.00')

        PortfolioTransaction.objects.create(user=self.user, stock=self.stock_b, transaction_type='BUY', quantity=2, price='100.00')
        PortfolioTransaction.objects.create(user=self.user, stock=self.stock_b, transaction_type='BUY', quantity=3, price='110.00')
        PortfolioTransaction.objects.create(user=self.user, stock=self.stock_b, transaction_type='SELL', quantity=1, price='120.00')

        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('portfolio:holdings'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['holdings']), 1)
        self.assertEqual(response.data['holdings'][0]['stock_id'], self.stock_b.id)
        self.assertEqual(response.data['holdings'][0]['symbol'], 'NLIC')
        self.assertEqual(response.data['holdings'][0]['quantity'], 4)
        self.assertEqual(response.data['holdings'][0]['average_purchase_price'], '106.00')

    def test_get_holdings_returns_only_the_authenticated_users_data(self):
        PortfolioTransaction.objects.create(user=self.user, stock=self.stock_a, transaction_type='BUY', quantity=4, price='200.00')
        PortfolioTransaction.objects.create(user=self.other_user, stock=self.stock_a, transaction_type='BUY', quantity=9, price='250.00')
        PortfolioTransaction.objects.create(user=self.other_user, stock=self.stock_b, transaction_type='BUY', quantity=2, price='300.00')

        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('portfolio:holdings'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['holdings']), 1)
        self.assertEqual(response.data['holdings'][0]['stock_id'], self.stock_a.id)
        self.assertEqual(response.data['holdings'][0]['quantity'], 4)

    def test_get_holdings_isolates_user_a_data_from_user_b(self):
        PortfolioTransaction.objects.create(user=self.user, stock=self.stock_a, transaction_type='BUY', quantity=10, price='500.00')
        PortfolioTransaction.objects.create(user=self.other_user, stock=self.stock_a, transaction_type='BUY', quantity=20, price='600.00')
        PortfolioTransaction.objects.create(user=self.other_user, stock=self.stock_c, transaction_type='BUY', quantity=5, price='700.00')

        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('portfolio:holdings'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['holdings']), 1)
        self.assertEqual(response.data['holdings'][0]['symbol'], 'NABIL')
        self.assertEqual(response.data['holdings'][0]['quantity'], 10)
        self.assertNotIn(20, [holding['quantity'] for holding in response.data['holdings']])
        self.assertNotIn('NICA', [holding['symbol'] for holding in response.data['holdings']])
        self.assertNotIn('NABIL', [holding['symbol'] for holding in response.data['holdings'] if holding['quantity'] == 20])

    def test_get_holdings_isolates_user_b_data_from_user_a(self):
        PortfolioTransaction.objects.create(user=self.user, stock=self.stock_a, transaction_type='BUY', quantity=10, price='500.00')
        PortfolioTransaction.objects.create(user=self.other_user, stock=self.stock_a, transaction_type='BUY', quantity=20, price='600.00')
        PortfolioTransaction.objects.create(user=self.other_user, stock=self.stock_c, transaction_type='BUY', quantity=5, price='700.00')

        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(reverse('portfolio:holdings'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['holdings']), 2)
        holdings_by_symbol = {holding['symbol']: holding for holding in response.data['holdings']}
        self.assertEqual(holdings_by_symbol['NABIL']['quantity'], 20)
        self.assertEqual(holdings_by_symbol['NICA']['quantity'], 5)
        self.assertNotIn('NABIL', [holding['symbol'] for holding in response.data['holdings'] if holding['quantity'] == 10])

    def test_get_holdings_requires_authentication(self):
        response = self.client.get(reverse('portfolio:holdings'))

        self.assertEqual(response.status_code, 401)


class PortfolioSummaryAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='alice',
            email='alice@example.com',
            password='password123',
        )
        self.other_user = User.objects.create_user(
            username='bob',
            email='bob@example.com',
            password='password123',
        )
        self.stock_a = Stock.objects.create(
            symbol='NABIL',
            company_name='Nabil Bank Limited',
            exchange='NEPSE',
            sector='Banking',
            industry='Banking',
            currency='NPR',
        )
        self.stock_b = Stock.objects.create(
            symbol='NLIC',
            company_name='Nepal Life Insurance',
            exchange='NEPSE',
            sector='Insurance',
            industry='Life Insurance',
            currency='NPR',
        )

    @patch('StockTracker.portfolio.views.get_current_price')
    def test_get_summary_returns_profitable_holdings_and_correct_overall_values(self, mock_get_current_price):
        PortfolioTransaction.objects.create(user=self.user, stock=self.stock_a, transaction_type='BUY', quantity=10, price='100.00')
        PortfolioTransaction.objects.create(user=self.user, stock=self.stock_a, transaction_type='BUY', quantity=5, price='120.00')
        PortfolioTransaction.objects.create(user=self.user, stock=self.stock_a, transaction_type='SELL', quantity=3, price='150.00')

        PortfolioTransaction.objects.create(user=self.user, stock=self.stock_b, transaction_type='BUY', quantity=4, price='50.00')
        PortfolioTransaction.objects.create(user=self.user, stock=self.stock_b, transaction_type='SELL', quantity=1, price='55.00')

        mock_get_current_price.side_effect = [
            {'current_price': 130.00},
            {'current_price': 60.00},
        ]

        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('portfolio:summary'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['portfolio_market_value'], '1740.00')
        self.assertEqual(response.data['summary']['total_investment_cost'], '1430.00')
        self.assertEqual(response.data['summary']['total_unrealized_pnl'], '310.00')
        self.assertEqual(response.data['summary']['total_pnl_percentage'], '21.68')

        holdings = response.data['holdings']
        self.assertEqual(len(holdings), 2)
        self.assertEqual(holdings[0]['symbol'], 'NABIL')
        self.assertEqual(holdings[0]['market_value'], '1560.00')
        self.assertEqual(holdings[0]['unrealized_pnl'], '280.00')
        self.assertEqual(holdings[0]['pnl_percentage'], '21.88')

    @patch('StockTracker.portfolio.views.get_current_price')
    def test_get_summary_handles_loss_making_holdings_and_missing_market_prices(self, mock_get_current_price):
        PortfolioTransaction.objects.create(user=self.user, stock=self.stock_a, transaction_type='BUY', quantity=10, price='100.00')
        PortfolioTransaction.objects.create(user=self.user, stock=self.stock_b, transaction_type='BUY', quantity=2, price='50.00')

        mock_get_current_price.side_effect = [
            {'current_price': 90.00},
            ValueError('No price data available for NLIC.'),
        ]

        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('portfolio:summary'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['portfolio_market_value'], '900.00')
        self.assertEqual(response.data['summary']['total_investment_cost'], '1000.00')
        self.assertEqual(response.data['summary']['total_unrealized_pnl'], '-100.00')
        self.assertEqual(response.data['summary']['total_pnl_percentage'], '-10.00')
        self.assertEqual(response.data['holdings'][0]['unrealized_pnl'], '-100.00')
        self.assertIsNone(response.data['holdings'][1]['market_price'])
        self.assertIsNone(response.data['holdings'][1]['market_value'])
        self.assertIsNone(response.data['holdings'][1]['unrealized_pnl'])

    @patch('StockTracker.portfolio.views.get_current_price')
    def test_get_summary_returns_only_authenticated_users_data(self, mock_get_current_price):
        PortfolioTransaction.objects.create(user=self.user, stock=self.stock_a, transaction_type='BUY', quantity=5, price='100.00')
        PortfolioTransaction.objects.create(user=self.other_user, stock=self.stock_a, transaction_type='BUY', quantity=8, price='110.00')
        PortfolioTransaction.objects.create(user=self.other_user, stock=self.stock_b, transaction_type='BUY', quantity=2, price='70.00')
        mock_get_current_price.return_value = {'current_price': 120.00}

        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('portfolio:summary'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['holdings']), 1)
        self.assertEqual(response.data['holdings'][0]['stock_id'], self.stock_a.id)
        self.assertEqual(response.data['summary']['portfolio_market_value'], '600.00')

    @patch('StockTracker.portfolio.views.get_current_price')
    def test_get_summary_returns_empty_for_empty_portfolio(self, mock_get_current_price):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('portfolio:summary'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['holdings'], [])
        self.assertEqual(response.data['summary']['portfolio_market_value'], '0.00')
        self.assertEqual(response.data['summary']['total_investment_cost'], '0.00')
        self.assertEqual(response.data['summary']['total_unrealized_pnl'], '0.00')
        self.assertEqual(response.data['summary']['total_pnl_percentage'], '0.00')
        mock_get_current_price.assert_not_called()

    def test_get_summary_requires_authentication(self):
        response = self.client.get(reverse('portfolio:summary'))

        self.assertEqual(response.status_code, 401)
