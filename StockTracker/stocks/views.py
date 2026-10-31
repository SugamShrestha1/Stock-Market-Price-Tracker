from django.db.models import Q
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Stock
from .serializers import StockSerializer


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
