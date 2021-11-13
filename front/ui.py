from rich.console import Console
import os
import random
import time
import sys
import tty

from rich.live import Live
from rich.prompt import Prompt
from rich.console import Console, Group, group
from rich.text import Text
from aioconsole import console

from rich.layout import Layout

from bullet import Bullet
from bullet import colors

from rich.panel import Panel
import asyncio


def dropdown(prompt, choices):
    cli = Bullet(
        prompt=prompt,
        choices=choices,
        indent=0,
        align=5,
        margin=2,
        bullet=">",
        bullet_color=colors.bright(colors.foreground["yellow"]),
        word_on_switch=colors.bright(colors.foreground["yellow"]),
        background_on_switch=colors.background["black"],
        pad_right=2
    )
    return cli.launch()


def parse_stream(stream):
    log = '\n'.join(f.strip() for f in stream)
    return Text(log, overflow="fold")


def command_input():
    # return Prompt("command: ")
    return Text("command: ")


def render(stream, console=None):
    layout = Layout()
    layout.split_column(
        Layout(Panel(parse_stream(stream)), name="output"),
        # Layout(Prompt.ask("console:"))
        # Layout(console)
        # Layout(command_input(), name="input", size=2)
    )
    return layout


def display(stream):
    with Live(render(stream), refresh_per_second=4) as live:
        while(True):
            live.update(render(stream))


class BlockingContext:
    '''A context manager set console.file blocking'''

    def __init__(self, console: 'NonBlockingConsole') -> None:
        self.file = console.file

    def __enter__(self) -> 'BlockingContext':
        os.set_blocking(self.file.fileno(), True)
        return self

    def __exit__(self, *exc_details) -> None:
        os.set_blocking(self.file.fileno(), False)


class NonBlockingConsole(Console):
    '''Support if NonBlocking stdout rich.console.Console
    '''

    def _check_buffer(self) -> None:
        with BlockingContext(self):
            super()._check_buffer()


async def async_rich_task(queue, stop_flag):
    tty.setcbreak(sys.stdin)
    console = NonBlockingConsole()
    data = []
    with Live(render(data, console),
              screen=True,
              # auto_refresh=False,
              refresh_per_second=4,
              console=console,
              redirect_stderr=False) as live:
        while not stop_flag.is_set():
            data.append(queue.get())
            live.update(render(data[-(console.height - 4):], console))
            # console.input()


def rich_task(queue, stop_flag):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(async_rich_task(queue, stop_flag))
    loop.close()
