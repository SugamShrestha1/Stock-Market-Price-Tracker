from django.contrib import admin
from .models import PortfolioTransaction


@admin.register(PortfolioTransaction)
class PortfolioTransactionAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'user',
        'stock',
        'transaction_type',
        'quantity',
        'price',
        'transaction_date',
        'created_at',
    )

    list_filter = (
        'transaction_type',
        'transaction_date',
    )

    search_fields = (
        'user__username',
        'stock__symbol',
    )

    readonly_fields = ('created_at',)