from rest_framework import serializers
from .models import WatchlistItem


class WatchlistItemSerializer(serializers.ModelSerializer):

    stock = serializers.SerializerMethodField()

    class Meta:
        model = WatchlistItem
        fields = ['id', 'stock', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_stock(self, obj):
        return {
            'id': obj.stock.id,
            'symbol': obj.stock.symbol,
            'company_name': obj.stock.company_name,
        }