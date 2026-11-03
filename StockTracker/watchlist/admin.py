from django.contrib import admin
from .models import WatchlistItem


@admin.register(WatchlistItem)
class WatchlistItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'stock', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'stock__symbol')
    readonly_fields = ('created_at',)