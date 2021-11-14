from textual.app import App
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from textual.reactive import Reactive
from textual.widget import Widget

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

class CommandInput(Widget):
    """ Widget that receives commands and sends them to Ornette """
    command = Reactive("")

    def reset_command(self):
      self.command = ""

    def on_key(self, event):
      key = event.key
      if key == 'enter':
        self.reset_command()
      elif key.startswith('ctrl'):
        if key == 'ctrl+h':
          self.command = self.command[:-1]

      else:
        self.command += key
        self.render()
        
    def render(self) -> Text:
      return Panel(Text(self.command), title="command", title_align="left", height=4)