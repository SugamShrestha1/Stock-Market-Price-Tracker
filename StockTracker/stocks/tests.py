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

