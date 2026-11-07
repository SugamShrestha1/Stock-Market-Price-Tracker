
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class PortfolioTransaction(models.Model):

    TRANSACTION_TYPES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='portfolio_transactions'
    )

    stock = models.ForeignKey(
        'stocks.Stock',
        on_delete=models.CASCADE,
        related_name='portfolio_transactions'
    )

    transaction_type = models.CharField(
        max_length=4,
        choices=TRANSACTION_TYPES
    )

    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    transaction_date = models.DateField(
        default=timezone.localdate
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-transaction_date', '-created_at']

    def __str__(self):
        return f"{self.user} - {self.transaction_type} {self.stock.symbol}"
