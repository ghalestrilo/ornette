from textual.app import App
from rich.text import Text
from rich.panel import Panel
from rich.align import Align

from textual.reactive import Reactive
from textual.app import App
from textual.widget import Widget
from datetime import datetime

class CommandInput(Widget):
    """ Widget that receives commands and sends them to Ornette """
    command = Reactive("")

    def reset_command(self):
      self.command = ""

    def on_key(self, event):
      key = event.key
      if key == 'enter':
        self.reset_command()

      else:
        self.command += key
        self.render()
        
    def render(self) -> Text:
      return Panel(Text(self.command), title="command", title_align="left", height=4)

class Engine(Widget):
    """ Class that runs the MDGS and renders its output """
    def on_mount(self):
        self.set_interval(1, self.refresh)

    def render(self):
        time = datetime.now().strftime("%c")
        return Panel(Align.center(time, vertical="middle"), title="output", title_align="left", )

class Front(App):
  input_widget = None
  
  def on_key(self, event):
    self.input_widget.on_key(event)
    
  async def on_mount(self) -> None:
    self.input_widget = CommandInput()
    await self.view.dock(Engine(), self.input_widget)













# from front.ui import dropdown, display, rich_task
# from front.container_manager import build_image, assert_image, run_image, run_client
# import threading
# from queue import Queue

# class Front():
#   def __init__(self,options):
#     self.queue = Queue()
#     self.stop_flag = threading.Event()
#     self.display_thread = threading.Thread(target=rich_task, args=(self.queue, self.stop_flag))
#     self.docker_thread = threading.Thread(target=run_image, args=(self.queue, options, self.stop_flag))
#     pass

#   def start(self):
#     self.display_thread.daemon=True
#     self.docker_thread.daemon=True
#     self.display_thread.start()
#     self.docker_thread.start()
#     self.stop_flag.wait()

    

#   def stop(self):
#     self.stop_flag.set()
#     self.docker_thread.join()
#     self.display_thread.join()
