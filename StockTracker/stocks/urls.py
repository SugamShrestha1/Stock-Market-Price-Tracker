from django.urls import path

from .views import (
    StockDetailView,
    StockHistoricalDataView,
    StockListView,
    StockPriceHistoryView,
    StockQuoteView,
)

app_name = 'stocks'

urlpatterns = [
    path('stocks/', StockListView.as_view(), name='stock-list'),
    path('stocks/<str:symbol>/quote/', StockQuoteView.as_view(), name='stock-quote'),
    path('stocks/<str:symbol>/history/', StockHistoricalDataView.as_view(), name='stock-historical-data'),
    path('stocks/<int:pk>/price-history/', StockPriceHistoryView.as_view(), name='stock-price-history'),
    path('stocks/<int:pk>/', StockDetailView.as_view(), name='stock-detail'),
]
