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
