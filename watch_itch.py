"""Client WebSocket simple pour visualiser le flux ITCH L3."""
import asyncio
import json
import sys
from datetime import datetime

import websockets


COLORS = {
    'ADD': '\033[94m',      # Blue
    'EXECUTE': '\033[95m',  # Magenta
    'CANCEL': '\033[91m',   # Red
    'RESET': '\033[0m',
    'BOLD': '\033[1m',
}


def format_msg(msg: dict) -> str:
    """Format un message ITCH pour l'affichage."""
    msg_type = msg['msg_type']
    color = COLORS.get(msg_type, '')
    
    if msg_type == 'ADD':
        return (
            f"{color}ADD{COLORS['RESET']} "
            f"#{msg['order_id']:>8} "
            f"{msg['side']:>3} "
            f"@{msg['price']:>7.2f} "
            f"x{msg['quantity']:>4}"
        )
    elif msg_type == 'EXECUTE':
        return (
            f"{color}EXEC{COLORS['RESET']} "
            f"maker=#{msg['maker_id']:>8} "
            f"@{msg['price']:>7.2f} "
            f"x{msg['quantity']:>4} "
            f"({msg['aggressor_side']})"
        )
    elif msg_type == 'CANCEL':
        return (
            f"{color}CANC{COLORS['RESET']} "
            f"#{msg['order_id']:>8} "
            f"{msg['side']:>3} "
            f"@{msg['price']:>7.2f} "
            f"qty={msg['cancelled_quantity']:>4}"
        )
    return str(msg)


async def watch_feed(url: str = 'ws://127.0.0.1:8000/ws', limit: int = 0):
    """Se connecte au flux ITCH et affiche les messages."""
    print(f"{COLORS['BOLD']}Connexion à {url}...{COLORS['RESET']}")
    
    try:
        async with websockets.connect(url) as ws:
            print(f"{COLORS['BOLD']}✅ Connecté!{COLORS['RESET']}\n")
            
            count = 0
            batch_num = 0
            
            while True:
                data = await ws.recv()
                batch = json.loads(data)
                batch_num += 1
                
                print(f"{COLORS['BOLD']}--- Batch {batch_num} ({len(batch)} msgs) ---{COLORS['RESET']}")
                
                for msg in batch:
                    print(format_msg(msg))
                    count += 1
                    
                    if limit > 0 and count >= limit:
                        print(f"\n{COLORS['BOLD']}Limite de {limit} messages atteinte.{COLORS['RESET']}")
                        return
                
                print()  # Ligne vide entre les batches
                
    except websockets.exceptions.ConnectionClosed:
        print(f"\n{COLORS['BOLD']}❌ Connexion fermée{COLORS['RESET']}")
    except KeyboardInterrupt:
        print(f"\n{COLORS['BOLD']}⏹️  Arrêté par l'utilisateur{COLORS['RESET']}")
    except Exception as e:
        print(f"\n{COLORS['BOLD']}❌ Erreur: {e}{COLORS['RESET']}")


if __name__ == '__main__':
    url = sys.argv[1] if len(sys.argv) > 1 else 'ws://127.0.0.1:8000/ws'
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    
    print(f"{COLORS['BOLD']}=== ITCH L3 Feed Monitor ==={COLORS['RESET']}")
    print(f"URL: {url}")
    if limit > 0:
        print(f"Limite: {limit} messages\n")
    else:
        print("Appuyez sur Ctrl+C pour arrêter\n")
    
    asyncio.run(watch_feed(url, limit))
