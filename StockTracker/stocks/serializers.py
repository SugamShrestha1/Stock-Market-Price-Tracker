from rest_framework import serializers

from .models import Stock


class StockSerializer(serializers.ModelSerializer):
    """Serializer for Stock model."""
    class Meta:
        model = Stock
        fields = ('id', 'symbol', 'company_name', 'exchange', 'sector', 'industry', 'currency')
        read_only_fields = ('id',)
