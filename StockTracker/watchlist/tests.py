from django.test import TestCase
from rest_framework.test import APIClient

from StockTracker.accounts.models import User
from StockTracker.stocks.models import Stock
from StockTracker.watchlist.models import WatchlistItem


class WatchlistAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='alice', email='alice@example.com', password='StrongPass123!')
        self.other_user = User.objects.create_user(username='bob', email='bob@example.com', password='StrongPass123!')
        self.stock_a = Stock.objects.create(
            symbol='AAPL',
            company_name='Apple Inc.',
            exchange='NASDAQ',
            sector='Technology',
            industry='Consumer Electronics',
            currency='USD',
        )
        self.stock_b = Stock.objects.create(
            symbol='MSFT',
            company_name='Microsoft Corporation',
            exchange='NASDAQ',
            sector='Technology',
            industry='Software - Infrastructure',
            currency='USD',
        )

    def test_get_watchlist_returns_only_authenticated_users_items(self):
        WatchlistItem.objects.create(user=self.user, stock=self.stock_a)
        WatchlistItem.objects.create(user=self.other_user, stock=self.stock_b)

        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/watchlist/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['stock']['id'], self.stock_a.id)

    def test_post_watchlist_creates_item_and_rejects_duplicate(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post('/api/watchlist/', {'stock': self.stock_a.id}, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(WatchlistItem.objects.filter(user=self.user, stock=self.stock_a).count(), 1)
        self.assertEqual(response.data['stock']['id'], self.stock_a.id)

        duplicate_response = self.client.post('/api/watchlist/', {'stock': self.stock_a.id}, format='json')

        self.assertEqual(duplicate_response.status_code, 400)
        self.assertIn('already', str(duplicate_response.data['error']).lower())

    def test_delete_watchlist_removes_only_authenticated_users_item(self):
        WatchlistItem.objects.create(user=self.user, stock=self.stock_a)
        WatchlistItem.objects.create(user=self.other_user, stock=self.stock_a)

        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/watchlist/{self.stock_a.id}/')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(WatchlistItem.objects.filter(user=self.user, stock=self.stock_a).exists())
        self.assertTrue(WatchlistItem.objects.filter(user=self.other_user, stock=self.stock_a).exists())

        missing_response = self.client.delete(f'/api/watchlist/{self.stock_b.id}/')

        self.assertEqual(missing_response.status_code, 404)
        self.assertIn('watchlist', str(missing_response.data['error']).lower())
