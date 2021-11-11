import random
import time

from typing import TextIO

from rich.live import Live
from rich.prompt import Prompt
from rich.console import Group, Console
from rich.table import Table

from rich.layout import Layout

from bullet import Bullet
from bullet import colors

from rich import print
from rich.panel import Panel


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
  # return '\n'.join(f.strip() for f in stream)
  return '\n'.join(f.strip() for f in stream)
  console = Console()
  with console.pager():
    console.print('\n'.join(f.strip() for f in stream))

def render(stream):
  layout = Layout()
  layout.split_column(
    Layout(parse_stream(stream),name="output"),
    Layout(parse_stream(stream),name="input",size=2)
  )
  return layout

def display(stream):
  with Live(render(stream), refresh_per_second=4) as live:
    while(True):
      live.update(render(stream))