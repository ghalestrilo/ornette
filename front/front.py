from textual.app import App
from rich.text import Text
from rich.panel import Panel
from rich.align import Align

from textual.app import App
from datetime import datetime
import os
import threading
from argparse import ArgumentParser

from front.container_manager import ScrollingTextDisplay
from front.ui import CommandInput
from front.ui import dropdown
from front.container_manager import build_image, run_client
from server.data import process_options

# Command-Line options
args = ArgumentParser()
args.add_argument('--modelname', type=str,
                  help="The improvisation model you want to run")
args.add_argument('--checkpoint', type=str, help="The checkpoint to be loaded")
args.add_argument('--rebuild', type=bool, default=False,
                  help="Force docker images to be rebuilt")
args.add_argument('--exec', type=str, default=None,
                  help="Startup command to run on the server")
args.add_argument("--no-server",     type=bool, default=False,
                  help="Run the model without starting an OSC server")
args.add_argument("--no-module",     type=bool, default=False,
                  help="Run ornette without a model")
# options = args.parse_args()

class Front(App):
    input_widget = None
    container_engine = None
    options = None

    def set_options(self, options):
        self.options = options

    def on_key(self, event):
        self.input_widget.on_key(event)

    async def on_shutdown_request(self):
      self.container_engine.stop()

    async def on_mount(self) -> None:
        options = process_options(args.parse_args(), dropdown)

        if options.checkpoint is None:
          await self.shutdown()
          exit()

        self.input_widget = CommandInput()
        self.container_engine = ScrollingTextDisplay()
        self.input_widget.set_logger(self.container_engine.append)
        self.container_engine.run_image(options)
        await self.view.dock(self.container_engine, edge="top")
        await self.view.dock(self.input_widget, size=3, edge="bottom",z=1)