from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from StockTracker.stocks.models import Stock
from .models import WatchlistItem
from .serializers import WatchlistItemSerializer


class WatchlistListCreateView(APIView):
    """List the authenticated user's watchlist and add a stock to it."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        watchlist_items = WatchlistItem.objects.filter(user=request.user).select_related('stock').order_by('-created_at')
        serializer = WatchlistItemSerializer(watchlist_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        stock_id = request.data.get('stock')
        if stock_id is None:
            return Response({'error': 'A stock ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            stock_id = int(stock_id)
        except (TypeError, ValueError):
            return Response({'error': 'Stock ID must be an integer.'}, status=status.HTTP_400_BAD_REQUEST)

        stock = get_object_or_404(Stock, pk=stock_id)

        if WatchlistItem.objects.filter(user=request.user, stock=stock).exists():
            return Response({'error': 'This stock is already in your watchlist.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                watchlist_item = WatchlistItem.objects.create(user=request.user, stock=stock)
        except IntegrityError:
            return Response({'error': 'This stock is already in your watchlist.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = WatchlistItemSerializer(watchlist_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class WatchlistDestroyView(APIView):
    """Remove a stock from the authenticated user's watchlist."""
    permission_classes = [IsAuthenticated]

    def delete(self, request, stock_id):
        stock = get_object_or_404(Stock, pk=stock_id)
        watchlist_item = WatchlistItem.objects.filter(user=request.user, stock=stock).first()

        if watchlist_item is None:
            return Response({'error': 'This stock is not in your watchlist.'}, status=status.HTTP_404_NOT_FOUND)

        watchlist_item.delete()
        return Response({'message': 'Stock removed from your watchlist.'}, status=status.HTTP_200_OK)
