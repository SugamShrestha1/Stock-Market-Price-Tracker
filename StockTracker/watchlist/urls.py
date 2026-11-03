from django.urls import path

from .views import WatchlistDestroyView, WatchlistListCreateView

app_name = 'watchlist'

urlpatterns = [
    path('watchlist/', WatchlistListCreateView.as_view(), name='watchlist-list-create'),
    path('watchlist/<int:stock_id>/', WatchlistDestroyView.as_view(), name='watchlist-delete'),
]
