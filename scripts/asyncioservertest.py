from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.dispatcher import Dispatcher
import asyncio


def filter_handler(address, *args):
    print(f"{address}: {args}")


dispatcher = Dispatcher()
dispatcher.map("/filter", filter_handler)

ip = "127.0.0.1"
port = 1337


async def countloop():
    """Example main loop that only runs for 10 iterations before finishing"""
    for i in range(10):
        print(f"Loop {i}")
        await asyncio.sleep(1)

def killa(server):
    server.close()

async def init_main():
    loop = asyncio.get_event_loop()
    server = AsyncIOOSCUDPServer((ip, port), dispatcher, loop)
    transport, protocol = await server.create_serve_endpoint()  # Create datagram endpoint and start serving

    queue = asyncio.Queue()
    loop.call_later(3, server)
        
    await countloop()  # Enter main loop of program
    transport.close()  # Clean up serve endpoint


asyncio.run(init_main())
print('haha')
