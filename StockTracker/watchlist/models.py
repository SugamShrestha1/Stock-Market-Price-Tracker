from django.conf import settings
from django.db import models


class WatchlistItem(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="watchlist_items"
    )

    stock = models.ForeignKey(
        "stocks.Stock",
        on_delete=models.CASCADE,
        related_name="watchlist_items"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "stock"],
                name="unique_user_stock_watchlist"
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.stock.symbol}"