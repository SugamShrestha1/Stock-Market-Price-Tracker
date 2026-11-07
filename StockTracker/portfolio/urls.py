from django.urls import path

from .views import PortfolioHoldingsView, PortfolioSummaryView, PortfolioTransactionListCreateView

app_name = 'portfolio'

urlpatterns = [
    path('portfolio/transactions/', PortfolioTransactionListCreateView.as_view(), name='transactions'),
    path('portfolio/holdings/', PortfolioHoldingsView.as_view(), name='holdings'),
    path('portfolio/summary/', PortfolioSummaryView.as_view(), name='summary'),
]
