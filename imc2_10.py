from datamodel import OrderDepth, TradingState, Order
from typing import List, Dict
import math

# Precomputed from your analysis
MEAN_STD = {
    'CROISSANT': (10068.51, 62.27),
    'JAM': (12698.52, 108.13),
    'DJEMBE': (4036.94, 77.45),
    'PICNIC_BASKET1': (78469.69, 525.29),
    'PICNIC_BASKET2': (46123.22, 373.92),
    'KELP': (6012.50, 76.68),
    'RAINFOREST_RESIN': (10461.79, 78.92),
    'SQUID_INK': (7941.21, 95.91),
}

POSITION_LIMITS = {
    'CROISSANT': 250,
    'JAM': 350,
    'DJEMBE': 60,
    'PICNIC_BASKET1': 60,
    'PICNIC_BASKET2': 100,
    'KELP': 50,
    'RAINFOREST_RESIN': 50,
    'SQUID_INK': 50,
}

class Trader:
    def run(self, state: TradingState):
        result = {}
        for product, order_depth in state.order_depths.items():
            if product not in MEAN_STD:
                continue
            mean, std = MEAN_STD[product]
            spread = 1  # Default min spread buffer

            if order_depth.buy_orders and order_depth.sell_orders:
                best_bid = max(order_depth.buy_orders)
                best_ask = min(order_depth.sell_orders)
                market_spread = best_ask - best_bid
                spread = max(spread, market_spread)

            buy_threshold = mean - std + spread
            sell_threshold = mean + std - spread

            position = state.position.get(product, 0)
            limit = POSITION_LIMITS[product]
            orders: List[Order] = []

            for ask, ask_vol in sorted(order_depth.sell_orders.items()):
                if ask < buy_threshold and position + abs(ask_vol) <= limit:
                    orders.append(Order(product, ask, -ask_vol))
                    position += abs(ask_vol)

            for bid, bid_vol in sorted(order_depth.buy_orders.items(), reverse=True):
                if bid > sell_threshold and position - abs(bid_vol) >= -limit:
                    orders.append(Order(product, bid, -bid_vol))
                    position -= abs(bid_vol)

            result[product] = orders

        return result, 0, ""
