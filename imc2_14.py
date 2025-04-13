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

        # Position limits
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

        # Basket composition
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
                if best_ask < mid - 1:
                    vol = -od.sell_orders[best_ask]
                    qty = min(limit - pos, vol)
                    if qty > 0:
                        orders.append(Order(product, best_ask, qty))
                if best_bid > mid + 1:
                    vol = od.buy_orders[best_bid]
                    qty = min(limit + pos, vol)
                    if qty > 0:
                        orders.append(Order(product, best_bid, -qty))
            return orders

        def imc11_strategy(product):
            STATS = {
                'RAINFOREST_RESIN': {'mean': 9999.99, 'std': 1.50},
                'SQUID_INK': {'mean': 1903.87, 'std': 68.17},
            }
            if product not in STATS:
                return []
            od = state.order_depths.get(product)
            if not od:
                return []
            mean = STATS[product]['mean']
            std = STATS[product]['std']
            spread = 0.5 if product == 'RAINFOREST_RESIN' else 1
            pos = positions.get(product, 0)
            limit = limits[product]
            best_bid = max(od.buy_orders.keys()) if od.buy_orders else None
            best_ask = min(od.sell_orders.keys()) if od.sell_orders else None
            buy_price = mean - std + spread
            sell_price = mean + std - spread
            orders = []
            if best_ask is not None and best_ask < buy_price:
                vol = min(-od.sell_orders[best_ask], limit - pos)
                if vol > 0:
                    orders.append(Order(product, best_ask, vol))
            if best_bid is not None and best_bid > sell_price:
                vol = min(od.buy_orders[best_bid], limit + pos)
                if vol > 0:
                    orders.append(Order(product, best_bid, -vol))
            return orders

        # Baskets
        fair_val1 = smooth_fair_value("PICNIC_BASKET1", compute_basket_fair_value(basket1))
        result["PICNIC_BASKET1"] = trade_basket("PICNIC_BASKET1", fair_val1, min_spread=5)

        # Standard products
        for prod in ["CROISSANTS", "JAMS", "DJEMBES", "KELP"]:
            result[prod] = trade_individual(prod)

        # Replaced with imc2_11 strategies
        result["SQUID_INK"] = imc11_strategy("SQUID_INK")
        result["RAINFOREST_RESIN"] = imc11_strategy("RAINFOREST_RESIN")

        return result, conversions, traderData