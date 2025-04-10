from datamodel import OrderDepth, TradingState, Order
from typing import List, Dict

class Trader:
    def __init__(self):
        # Hardcoded historical stats based on analysis
        self.stats = {
            "KELP": {"mean": 2031, "std": 1.2, "z_entry": 1.0, "z_exit": 0.3},
            "SQUID_INK": {"mean": 1972, "std": 4.5, "z_entry": 1.5, "z_exit": 0.3},
            "RAINFOREST_RESIN": {"mean": 10000, "std": 2.5, "z_entry": 1.7, "z_exit": 0.2}
        }
        self.position_limit = 50

    def run(self, state: TradingState):
        result = {}

        for product, order_depth in state.order_depths.items():
            if product not in self.stats:
                continue

            stats = self.stats[product]
            mean = stats["mean"]
            std = stats["std"]
            z_entry = stats["z_entry"]
            z_exit = stats["z_exit"]
            position = state.position.get(product, 0)

            orders: List[Order] = []

            # Best bid/ask
            best_bid = max(order_depth.buy_orders.keys(), default=None)
            best_ask = min(order_depth.sell_orders.keys(), default=None)

            # Mid price for z-score calc
            if best_bid is not None and best_ask is not None:
                mid_price = (best_bid + best_ask) / 2
                z_score = (mid_price - mean) / std
            else:
                continue

            # Dynamic sizing: larger size for extreme Z
            size = 10
            if abs(z_score) > 2:
                size = 20
            pos_left = self.position_limit - abs(position)
            size = min(size, pos_left)

            # Entry: Buy if undervalued
            if z_score < -z_entry and position + size <= self.position_limit:
                orders.append(Order(product, int(best_ask), size))

            # Entry: Sell if overvalued
            elif z_score > z_entry and position - size >= -self.position_limit:
                orders.append(Order(product, int(best_bid), -size))

            # Exit: Mean reversion zone
            elif -z_exit <= z_score <= z_exit:
                if position > 0:
                    orders.append(Order(product, int(best_bid), -position))
                elif position < 0:
                    orders.append(Order(product, int(best_ask), -position))

            result[product] = orders

        return result, 0, ""