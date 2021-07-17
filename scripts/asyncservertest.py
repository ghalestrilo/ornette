from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.dispatcher import Dispatcher
import asyncio


def filter_handler(address, *args):
    print(f"{address}: {args}")


dispatcher = Dispatcher()
dispatcher.map("/filter", filter_handler)

ip = "127.0.0.1"
port = 1337


async def countloop(event):
    """Example main loop that only runs for 10 iterations before finishing"""
    for i in range(5):
        if event.is_set(): return
        print(f"Loop {i}")
        await asyncio.sleep(1)

def killa(transport, event):
  transport.close()
  event.set()

async def init_main():
    loop = asyncio.get_event_loop()
    server = AsyncIOOSCUDPServer((ip, port), dispatcher, loop)
    queue = asyncio.Queue()
    stopevent = asyncio.Event()  

    transport, protocol = await server.create_serve_endpoint()  # Create datagram endpoint and start serving
    loop.call_later(0.0002, killa, transport, stopevent)
    await countloop(stopevent)  # Enter main loop of program
    # transport.close()  # Clean up serve endpoint


asyncio.run(init_main())
