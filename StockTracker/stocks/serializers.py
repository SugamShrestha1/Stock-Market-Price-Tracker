from rest_framework import serializers

from .models import Stock, StockPrice


class StockSerializer(serializers.ModelSerializer):
    """Serializer for Stock model."""
    class Meta:
        model = Stock
        fields = ('id', 'symbol', 'company_name', 'exchange', 'sector', 'industry', 'currency')
        read_only_fields = ('id',)


class StockPriceSerializer(serializers.ModelSerializer):
    """Serializer for StockPrice model."""
    class Meta:
        model = StockPrice
        fields = ('id', 'stock', 'open_price', 'close_price', 'high_price', 'low_price', 'volume', 'recorded_at')
        read_only_fields = ('id',)
