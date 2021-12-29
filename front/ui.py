from textual.app import App
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from textual.reactive import Reactive
from textual.widget import Widget

from front.client import FrontClient

# TODO: Use Textual
from bullet import Bullet
from bullet import colors
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

default_options = {
  "sc_ip": '127.0.0.1',
  "sc_port": 5005
}

class CommandInput(Widget):
    """ Widget that receives commands and sends them to Ornette """
    command = Reactive("")
    client = FrontClient(default_options)

    def set_logger(self, logger):
      self.client.set_logger(logger)

    def reset_command(self):
      self.command = ""

    def on_key(self, event):
      key = event.key
      if key == 'enter':
        cmd = self.command.split(' ')
        self.client.send(cmd)
        # if cmd > [] and cmd[0] in ['end', 'exit', 'quit']: self.shutdown()
        self.reset_command()
      elif key.startswith('ctrl'):
        if key == 'ctrl+h':
          self.command = self.command[:-1]
      else:
        self.command += key
        self.render()
        
    def render(self) -> Text:
      return Panel(Text(self.command), title="command", title_align="left", height=3)

    async def on_shutdown_request(self):
      self.client.send_message(['/end'])