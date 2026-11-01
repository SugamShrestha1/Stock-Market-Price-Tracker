import requests
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Stock
from .serializers import StockPriceSerializer, StockSerializer
from .services import get_current_price, get_historical_prices


class StockListView(ListAPIView):
    """List all stocks with optional search and filtering."""
    queryset = Stock.objects.all().order_by('symbol')
    serializer_class = StockSerializer
    permission_classes = [AllowAny]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        queryset = Stock.objects.all().order_by('symbol')
        search = self.request.query_params.get('search', '').strip()
        exchange = self.request.query_params.get('exchange', '').strip()
        sector = self.request.query_params.get('sector', '').strip()
        industry = self.request.query_params.get('industry', '').strip()
        currency = self.request.query_params.get('currency', '').strip()

        if search:
            queryset = queryset.filter(
                Q(symbol__icontains=search) |
                Q(company_name__icontains=search) |
                Q(exchange__icontains=search) |
                Q(sector__icontains=search) |
                Q(industry__icontains=search) |
                Q(currency__icontains=search)
            )

        if exchange:
            queryset = queryset.filter(exchange__icontains=exchange)
        if sector:
            queryset = queryset.filter(sector__icontains=sector)
        if industry:
            queryset = queryset.filter(industry__icontains=industry)
        if currency:
            queryset = queryset.filter(currency__icontains=currency)

        return queryset.order_by('symbol')


class StockDetailView(RetrieveAPIView):
    """Retrieve one stock by ID."""
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [AllowAny]


class StockQuoteView(APIView):
    """Fetch the latest quote for a stock symbol."""
    permission_classes = [AllowAny]

    def get(self, request, symbol):
        try:
            quote = get_current_price(symbol)
            return Response(quote, status=status.HTTP_200_OK)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except requests.RequestException:
            return Response(
                {"error": "Unable to fetch stock data from Finnhub."},
                status=status.HTTP_502_BAD_GATEWAY
            )


class StockHistoricalDataView(APIView):
    """Fetch historical candle data for a stock symbol."""
    permission_classes = [AllowAny]

    def get(self, request, symbol):
        resolution = request.query_params.get('resolution', 'D') or 'D'
        from_param = request.query_params.get('from')
        to_param = request.query_params.get('to')

        if not from_param or not to_param:
            return Response(
                {"error": "Both 'from' and 'to' query parameters are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from_timestamp = int(from_param)
            to_timestamp = int(to_param)
        except (TypeError, ValueError):
            return Response(
                {"error": "'from' and 'to' must be valid Unix timestamps."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if from_timestamp >= to_timestamp:
            return Response(
                {"error": "'from' must be earlier than 'to'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            historical_data = get_historical_prices(
                symbol=symbol,
                resolution=resolution,
                from_timestamp=from_timestamp,
                to_timestamp=to_timestamp,
            )
            return Response(historical_data, status=status.HTTP_200_OK)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except requests.RequestException:
            return Response(
                {"error": "The Finnhub service is unavailable."},
                status=status.HTTP_502_BAD_GATEWAY,
            )


class StockPriceHistoryView(ListAPIView):
    """List historical price records for a stock."""
    serializer_class = StockPriceSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        stock = get_object_or_404(Stock, pk=self.kwargs.get('pk'))
        return stock.price_history.all().order_by('recorded_at')


class HomeView(APIView):
    """Simple root endpoint to avoid 404 on the project homepage."""
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "message": "StockTracker API is running.",
                "routes": {
                    "admin": "/admin/",
                    "api": "/api/"
                }
            },
            status=status.HTTP_200_OK
        )
