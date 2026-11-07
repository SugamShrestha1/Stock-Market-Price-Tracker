from decimal import Decimal, ROUND_HALF_UP

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from StockTracker.stocks.services import get_current_price
from .models import PortfolioTransaction
from .serializers import PortfolioTransactionSerializer


def calculate_user_holdings(user):
    """Return the authenticated user's current holdings using weighted-average cost accounting."""
    transactions = PortfolioTransaction.objects.filter(user=user).select_related('stock').order_by(
        'transaction_date',
        'created_at',
    )

    grouped_holdings = {}
    for transaction in transactions:
        stock_id = transaction.stock_id
        stock = transaction.stock

        if stock_id not in grouped_holdings:
            grouped_holdings[stock_id] = {
                'stock_id': stock_id,
                'symbol': stock.symbol,
                'company_name': stock.company_name,
                'total_bought': 0,
                'total_sold': 0,
                'quantity': 0,
                'cost_basis': Decimal('0.00'),
            }

        holding = grouped_holdings[stock_id]

        if transaction.transaction_type == 'BUY':
            holding['total_bought'] += transaction.quantity
            holding['quantity'] += transaction.quantity
            holding['cost_basis'] += Decimal(transaction.quantity) * Decimal(transaction.price)
        elif transaction.transaction_type == 'SELL':
            holding['total_sold'] += transaction.quantity
            remaining_quantity = holding['quantity']
            if remaining_quantity <= 0:
                continue

            sell_quantity = min(transaction.quantity, remaining_quantity)
            if sell_quantity <= 0:
                continue

            average_cost_per_share = holding['cost_basis'] / Decimal(remaining_quantity)
            sold_cost_basis = average_cost_per_share * Decimal(sell_quantity)

            holding['cost_basis'] -= sold_cost_basis
            holding['quantity'] -= sell_quantity

    holdings = []
    for holding in grouped_holdings.values():
        if holding['quantity'] <= 0:
            continue

        average_purchase_price = (holding['cost_basis'] / Decimal(holding['quantity'])).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP,
        )

        exact_cost_basis = holding['cost_basis'].quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        holdings.append({
            'stock_id': holding['stock_id'],
            'symbol': holding['symbol'],
            'company_name': holding['company_name'],
            'total_bought': holding['total_bought'],
            'total_sold': holding['total_sold'],
            'quantity': holding['quantity'],
            'average_purchase_price': str(average_purchase_price),
            'investment_cost': str(exact_cost_basis),
        })

    return holdings


class PortfolioTransactionListCreateView(APIView):
    """List the authenticated user's portfolio transactions and create new ones."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        transactions = PortfolioTransaction.objects.filter(user=request.user).select_related('stock')
        serializer = PortfolioTransactionSerializer(transactions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = PortfolioTransactionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PortfolioHoldingsView(APIView):
    """Return the authenticated user's current holdings using weighted-average cost accounting."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        holdings = calculate_user_holdings(request.user)
        return Response({'holdings': holdings}, status=status.HTTP_200_OK)


class PortfolioSummaryView(APIView):
    """Return the authenticated user's portfolio summary with current market value and P/L."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        holdings = calculate_user_holdings(request.user)

        portfolio_market_value = Decimal('0.00')
        total_investment_cost = Decimal('0.00')
        total_unrealized_pnl = Decimal('0.00')

        enriched_holdings = []
        for holding in holdings:
            symbol = holding['symbol']
            quantity = Decimal(holding['quantity'])
            average_purchase_price = Decimal(holding['average_purchase_price'])
            investment_cost = Decimal(holding['investment_cost'])

            try:
                quote = get_current_price(symbol)
                market_price = Decimal(str(quote['current_price'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            except (ValueError, TypeError):
                market_price = None
                market_value = None
                unrealized_pnl = None
                pnl_percentage = None
            else:
                market_value = (quantity * market_price).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                unrealized_pnl = (market_value - investment_cost).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                pnl_percentage = (unrealized_pnl / investment_cost * Decimal('100')) if investment_cost else Decimal('0.00')
                portfolio_market_value += market_value
                total_investment_cost += investment_cost
                total_unrealized_pnl += unrealized_pnl

            enriched_holdings.append({
                'stock_id': holding['stock_id'],
                'symbol': symbol,
                'company_name': holding['company_name'],
                'quantity': holding['quantity'],
                'average_purchase_price': holding['average_purchase_price'],
                'total_remaining_cost': holding['investment_cost'],
                'investment_cost': holding['investment_cost'],
                'market_price': str(market_price) if market_price is not None else None,
                'market_value': str(market_value) if market_value is not None else None,
                'unrealized_pnl': str(unrealized_pnl) if unrealized_pnl is not None else None,
                'pnl_percentage': str(pnl_percentage.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)) if pnl_percentage is not None else None,
            })

        if total_investment_cost:
            total_pnl_percentage = (total_unrealized_pnl / total_investment_cost * Decimal('100')).quantize(
                Decimal('0.01'),
                rounding=ROUND_HALF_UP,
            )
        else:
            total_pnl_percentage = Decimal('0.00')

        summary = {
            'portfolio_market_value': str(portfolio_market_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            'total_investment_cost': str(total_investment_cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            'total_unrealized_pnl': str(total_unrealized_pnl.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            'total_pnl_percentage': str(total_pnl_percentage.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
        }

        return Response({'summary': summary, 'holdings': enriched_holdings}, status=status.HTTP_200_OK)
