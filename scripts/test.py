import asyncio
import itertools
async def worker(evt):
    while True:
        await evt.wait()
        evt.clear()
        if evt.last_command is None:
            continue
        last_command = evt.last_command
        evt.last_command = None
        # execute last_command, possibly with timeout
        print(last_command)

async def main():
    evt = asyncio.Event()
    workers = [asyncio.create_task(worker(evt)) for _ in range(5)]
    for i in itertools.count():
        await asyncio.sleep(1)
        evt.last_command = f"foo {i}"
        evt.set()

asyncio.run(main())
