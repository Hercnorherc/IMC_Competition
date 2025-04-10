from datamodel import OrderDepth, TradingState, Order
from typing import List, Dict
import numpy as np

class Trader:
    def __init__(self):
        self.fair_value_history = {"PICNIC_BASKET1": [], "PICNIC_BASKET2": []}
        self.window = 10  # For fair value smoothing

    def run(self, state: TradingState):
        result = {}
        conversions = 0
        traderData = state.traderData

        # Position limits for all known products
        limits = {
            "CROISSANTS": 250,
            "JAMS": 350,
            "DJEMBES": 60,
            "PICNIC_BASKET1": 60,
            "PICNIC_BASKET2": 100,
            "SQUID_INK": 50,
            "KELP": 50,
            "RAINFOREST_RESIN": 50
        }
        positions = state.position

        # Composition references for fair value estimation
        basket1 = {'CROISSANTS': 6, 'JAMS': 3, 'DJEMBES': 1}
        basket2 = {'CROISSANTS': 4, 'JAMS': 2}

        def get_mid_price(product):
            od = state.order_depths.get(product)
            if od and od.buy_orders and od.sell_orders:
                best_bid = max(od.buy_orders)
                best_ask = min(od.sell_orders)
                return (best_bid + best_ask) / 2
            return None

        def compute_basket_fair_value(basket):
            value = 0
            for item, qty in basket.items():
                mid = get_mid_price(item)
                if mid is not None:
                    value += qty * mid
            return value

        def smooth_fair_value(name, new_value):
            history = self.fair_value_history.setdefault(name, [])
            history.append(new_value)
            if len(history) > self.window:
                history.pop(0)
            return np.mean(history)

        def trade_basket(basket_name, basket_value, min_spread):
            orders = []
            od = state.order_depths.get(basket_name)
            if not od:
                return orders
            pos = positions.get(basket_name, 0)
            limit = limits[basket_name]
            if od.sell_orders:
                best_ask = min(od.sell_orders)
                vol = -od.sell_orders[best_ask]
                if best_ask < basket_value - min_spread:
                    qty = min(limit - pos, vol)
                    if qty > 0:
                        orders.append(Order(basket_name, best_ask, qty))
            if od.buy_orders:
                best_bid = max(od.buy_orders)
                vol = od.buy_orders[best_bid]
                if best_bid > basket_value + min_spread:
                    qty = min(limit + pos, vol)
                    if qty > 0:
                        orders.append(Order(basket_name, best_bid, -qty))
            return orders

        def trade_individual(product):
            orders = []
            od = state.order_depths.get(product)
            if not od:
                return orders
            pos = positions.get(product, 0)
            limit = limits.get(product, 100)
            if od.buy_orders and od.sell_orders:
                best_bid = max(od.buy_orders)
                best_ask = min(od.sell_orders)
                mid = (best_bid + best_ask) / 2
                # Buy if underpriced
                if best_ask < mid - 1:
                    vol = -od.sell_orders[best_ask]
                    qty = min(limit - pos, vol)
                    if qty > 0:
                        orders.append(Order(product, best_ask, qty))
                # Sell if overpriced
                if best_bid > mid + 1:
                    vol = od.buy_orders[best_bid]
                    qty = min(limit + pos, vol)
                    if qty > 0:
                        orders.append(Order(product, best_bid, -qty))
            return orders

        def market_make_resin():
            orders = []
            product = "RAINFOREST_RESIN"
            limit = limits[product]
            pos = positions.get(product, 0)
            od = state.order_depths.get(product)
            if not od:
                return orders

            spread = 1
            if od.buy_orders and od.sell_orders:
                best_bid = max(od.buy_orders)
                best_ask = min(od.sell_orders)
                if best_ask - best_bid > spread:
                    fair = (best_bid + best_ask) / 2
                    buy_price = int(fair - 1)
                    sell_price = int(fair + 1)
                    qty_buy = min(5, limit - pos)
                    qty_sell = min(5, limit + pos)
                    if qty_buy > 0:
                        orders.append(Order(product, buy_price, qty_buy))
                    if qty_sell > 0:
                        orders.append(Order(product, sell_price, -qty_sell))
            return orders

        # Compute and smooth fair values
        fair_val1 = smooth_fair_value("PICNIC_BASKET1", compute_basket_fair_value(basket1))
        fair_val2 = smooth_fair_value("PICNIC_BASKET2", compute_basket_fair_value(basket2))

        # Trade baskets with thresholds
        result["PICNIC_BASKET1"] = trade_basket("PICNIC_BASKET1", fair_val1, min_spread=5)
        result["PICNIC_BASKET2"] = trade_basket("PICNIC_BASKET2", fair_val2, min_spread=10)

        # Trade individual products including new ones
        for prod in ["CROISSANTS", "JAMS", "DJEMBES", "SQUID_INK", "KELP"]:
            result[prod] = trade_individual(prod)

        # Market making for resin
        result["RAINFOREST_RESIN"] = market_make_resin()

        return result, conversions, traderData