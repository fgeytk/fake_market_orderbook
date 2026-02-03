from core import Orderbook, OrderType, Side
from simulation.agents import (
    AgentContext,
    MarketMaker,
    MomentumTrader,
    MeanReversionTrader,
    NoiseTrader,
    generate_agent_orders,
)


def base_ctx() -> AgentContext:
    book = Orderbook()
    return AgentContext(
        t=0,
        mid_price=10.0,
        mid_tick=book.price_to_tick(10.0),
        best_bid=None,
        best_ask=None,
        momentum=0.0,
    )


def test_market_maker_generates_two_limits():
    book = Orderbook()
    ctx = base_ctx()
    orders, next_id = MarketMaker(spread_ticks=2, size=5).generate_orders(book, ctx, next_id=1)
    assert len(orders) == 2
    assert orders[0].type == OrderType.LIMIT
    assert orders[1].type == OrderType.LIMIT
    assert next_id == 3


def test_momentum_trader_threshold():
    book = Orderbook()
    ctx = base_ctx()
    ctx.momentum = 0.0
    orders, _ = MomentumTrader(threshold=0.01, size=5).generate_orders(book, ctx, next_id=1)
    assert orders == []

    ctx.momentum = 0.02
    orders, _ = MomentumTrader(threshold=0.01, size=5).generate_orders(book, ctx, next_id=1)
    assert len(orders) == 1
    assert orders[0].side == Side.BID
    assert orders[0].type == OrderType.MARKET


def test_mean_reversion_trader_threshold():
    book = Orderbook()
    ctx = base_ctx()
    ctx.mid_price = 10.5
    orders, _ = MeanReversionTrader(ref_price=10.0, threshold=0.02, size=5).generate_orders(book, ctx, next_id=1)
    assert len(orders) == 1
    assert orders[0].side == Side.ASK


def test_noise_trader_alternates_side():
    book = Orderbook()
    ctx = base_ctx()
    trader = NoiseTrader(size=3, spread_ticks=4)

    orders, _ = trader.generate_orders(book, ctx, next_id=2)
    assert len(orders) == 1
    assert orders[0].side == Side.BID

    orders, _ = trader.generate_orders(book, ctx, next_id=3)
    assert len(orders) == 1
    assert orders[0].side == Side.ASK


def test_generate_agent_orders_aggregates():
    book = Orderbook()
    ctx = base_ctx()
    agents = [MarketMaker(), NoiseTrader()]

    orders, next_id = generate_agent_orders(agents, book, ctx, next_id=1)
    assert len(orders) == 3
    assert next_id >= 4
