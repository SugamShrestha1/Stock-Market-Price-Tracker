from rest_framework import serializers
from .models import PortfolioTransaction


class PortfolioTransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = PortfolioTransaction
        fields = [
            'id',
            'stock',
            'transaction_type',
            'quantity',
            'price',
            'transaction_date',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']