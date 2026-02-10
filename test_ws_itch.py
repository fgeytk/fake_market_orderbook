"""Test WebSocket ITCH L3 feed."""
if __name__ != "__main__":
    import pytest

    pytest.skip(
        "Manual integration test. Run directly: python test_ws_itch.py",
        allow_module_level=True,
    )

import asyncio
import json
import websockets


async def test():
    async with websockets.connect('ws://127.0.0.1:8000/ws') as ws:
        batch = json.loads(await ws.recv())
        print(f'✅ Reçu {len(batch)} messages ITCH L3')
        print('\nPremiers messages:')
        for msg in batch[:5]:
            msg_type = msg['msg_type']
            price = msg.get('price', 'N/A')
            qty = msg.get('quantity', msg.get('cancelled_quantity', 'N/A'))
            print(f"  {msg_type}: price={price}, qty={qty}")


if __name__ == '__main__':
    asyncio.run(test())
