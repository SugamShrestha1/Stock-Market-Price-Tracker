from django.db import models


class Stock(models.Model):
    id = models.AutoField(primary_key=True)
    symbol = models.CharField(max_length=20, unique=True)
    company_name = models.CharField(max_length=255)
    exchange = models.CharField(max_length=100)
    sector = models.CharField(max_length=100)
    industry = models.CharField(max_length=100)
    currency = models.CharField(max_length=20)

    class Meta:
        verbose_name = 'Stock'
        verbose_name_plural = 'Stocks'

    def __str__(self):
        return f"{self.symbol} - {self.company_name}"


class StockPrice(models.Model):
    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name='price_history'
    )
    open_price = models.DecimalField(max_digits=15, decimal_places=4)
    close_price = models.DecimalField(max_digits=15, decimal_places=4)
    high_price = models.DecimalField(max_digits=15, decimal_places=4)
    low_price = models.DecimalField(max_digits=15, decimal_places=4)
    volume = models.BigIntegerField(null=True, blank=True)
    recorded_at = models.DateTimeField()

    class Meta:
        verbose_name = 'Stock Price'
        verbose_name_plural = 'Stock Prices'

    def __str__(self):
        return f"{self.stock.symbol} - {self.recorded_at.date()}"
