from django.contrib import admin

from .models import Stock


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'company_name', 'exchange', 'sector', 'industry', 'currency')
    search_fields = ('symbol', 'company_name', 'exchange')
    list_filter = ('exchange', 'sector', 'industry')
