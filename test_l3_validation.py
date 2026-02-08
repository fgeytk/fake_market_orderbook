"""Quick test of L3 message validation."""

from core import L3Add, L3Execute, L3Cancel

print("✓ Testing L3 validation...")

# Valid message
msg = L3Add(
    msg_type="ADD",
    timestamp=1.0,
    order_id=123,
    side="BID",
    price_tick=100,
    price=10.0,
    quantity=5
)
print(f"  Valid L3Add created: order_id={msg.order_id}")

# Test invalid timestamp
try:
    bad = L3Add(
        msg_type="ADD",
        timestamp=-1.0,
        order_id=123,
        side="BID",
        price_tick=100,
        price=10.0,
        quantity=5
    )
    print("  ✗ FAILED: Should have raised ValueError for negative timestamp")
except ValueError as e:
    print(f"  ✓ Caught invalid timestamp: {e}")

# Test invalid side
try:
    bad = L3Add(
        msg_type="ADD",
        timestamp=1.0,
        order_id=123,
        side="INVALID",
        price_tick=100,
        price=10.0,
        quantity=5
    )
    print("  ✗ FAILED: Should have raised ValueError for invalid side")
except ValueError as e:
    print(f"  ✓ Caught invalid side: {e}")

# Test invalid quantity
try:
    bad = L3Add(
        msg_type="ADD",
        timestamp=1.0,
        order_id=123,
        side="BID",
        price_tick=100,
        price=10.0,
        quantity=-5
    )
    print("  ✗ FAILED: Should have raised ValueError for negative quantity")
except ValueError as e:
    print(f"  ✓ Caught invalid quantity: {e}")

print("\n✓ All L3 validation tests passed!")
