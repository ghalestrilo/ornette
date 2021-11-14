from textual.app import App
from rich.text import Text
from rich.panel import Panel
from rich.align import Align

from textual.app import App
from datetime import datetime

import threading
from front.container_manager import ContainerEngine
from front.ui import CommandInput

class Front(App):
  input_widget = None
  options = None

  def set_options(self, options):
    self.options = options
  
  def on_key(self, event):
    self.input_widget.on_key(event)
    
  async def on_mount(self) -> None:
    self.input_widget = CommandInput()
    container_engine = ContainerEngine()
    container_engine.run_image(self.options)
    print(self.options)
    await self.view.dock(
      container_engine
      , self.input_widget)