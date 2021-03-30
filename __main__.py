import os
import sys

# Move to utils.py?
def load_folder(name):
  sys.path.append(os.path.join(sys.path[0], name))

load_folder('src')

import numpy as np
import pickle
import time
import math



from threading import Thread, Event


from args import get_args
from server import Server, state, play

import pretty_errors

pretty_errors.configure(
    separator_character = '*',
    filename_display    = pretty_errors.FILENAME_EXTENDED,
    line_number_first   = True,
    display_link        = True,
    lines_before        = 5,
    lines_after         = 2,
    line_color          = pretty_errors.RED + '> ' + pretty_errors.default_config.line_color,
    code_color          = '  ' + pretty_errors.default_config.line_color,
    truncate_code       = True,
    display_locals      = True
)

pretty_errors.replace_stderr()

CODE_REBOOT=2222

os.environ['CUDA_VISIBLE_DEVICES'] = '0'

# TODO: Move to playback.py
class Clock(Thread):
    def __init__(self):
      Thread.__init__(self)
      self.stopped = Event()
      self.wait_for_more = False
      self.state = None

    def bind(self,server_state):
      self.state = server_state
      self.state['playhead'] = 0

    def stop(self):
      self.stopped.set()

    def generate(self):
      seq = self.state['model'].tick()[-128:]
      self.state['playhead'] = self.state['playhead'] - self.state['buffer_length'] + (len(seq) - len(self.state['history'][0]))
      self.state['playhead'] = max(self.state['playhead'], 0)
      self.state['history'][0] = seq
      self.wait_for_more = False

    def generate_in_background(self):
      Thread(target=self.generate).start()

    def has_history(self):
      hist = self.state['history']
      # return np.any(hist) and np.any(hist[0])
      return any(hist) and any(hist[0])

    def get_next_token(self):
      hist = self.state['history']

      if (self.has_history() == False):
        return None

      if (self.state['playhead'] >= len(hist[0])):
        self.wait_for_more = True
        return None

      # return self.state['model'].decode(self.state['history'][0][self.state['playhead']])
      return self.state['history'][0][self.state['playhead']]

    def process_next_token(self):
      e = self.get_next_token()

      if (e == None):
        print("No event / history is empty")
        return

      action = self.state['model'].get_action(e)
      if (action is None):
          print(f'No action returned for event {e}')
          return

      for (name, value) in action:
        if (name == 'play'): play(int(value))
        if (name == 'wait'): self.state['until_next_event'] = value

      self.state['playhead'] = self.state['playhead'] + 1


    def run(self):
      model = self.state['model']

      self.generate_in_background()
      while not self.stopped.wait(self.state['until_next_event']):
        if (self.state['is_running'] == True and self.wait_for_more == False):
          self.process_next_token()

          if(len(self.state['history'][0]) == 0):
            self.generate_in_background()
            return

          if (self.state['playhead'] / len(self.state['history'][0]) > self.state['trigger_generate']):
            if (self.state['debug_output'] == True):
              print("Generating more tokens ({} /{} > {})".format(self.state['playhead'], len(self.state['history'][0]), self.state['trigger_generate']))            
            self.generate_in_background()

            if (self.state['debug_output'] == True):
              print('history: {}'.format([model.decode(h) for h in self.state['history'][0]]))

# TODO: Move to init.py
import tensorflow as tf
import yaml
import urllib.request as req
import os
def download_checkpoint(name, url, force=False):
  checkpoint_dir = '/ckpt'
  ckptpath = os.path.normpath(f'{checkpoint_dir}/{name}')
  if os.path.exists(ckptpath) and not force:
    return
  response = req.urlopen(url, timeout = 5)
  content = response.read()
  with open(ckptpath, 'wb' ) as f:
    f.write( content )
    f.close()

def prep_module():
  with open(os.path.normpath('/model/.ornette.yml')) as file:
    moduleconfig = yaml.load_all(file, Loader=yaml.FullLoader)
    #
    for pair in moduleconfig:
      for k, v in pair.items():
        if k == "checkpoints":
          for checkpoint_name, checkpoint_url in v.items():
            print(f'downloading  {checkpoint_name}, "{checkpoint_url}"')
            download_checkpoint(checkpoint_name, checkpoint_url, False)
        print(k, ' -> ', v)

def load_model(checkpoint=None):
  if checkpoint is None:
    print("Please provide a checkpoint for the model to load")
    exit(-1)

  model_path = '/model'
  load_folder(model_path)
  from ornette import OrnetteModule
  return OrnetteModule(state, checkpoint=checkpoint)
# /TODO


# Main
if __name__ == "__main__":
    args = get_args()

    prep_module()

    # Prep Model
    model = load_model(args.checkpoint)

    # Start Server
    clock = Clock()
    server = Server(model, args, clock)
    clock.bind(state)

    clock.start()
    server.serve_forever()
    clock.stop()
    model.close()


    # if (state['return']==CODE_REBOOT):
    #   print("Should Reboot")
    # state['return']



## Steps to refactor

# 1. Refactor args (cause it's easy)
# 2. Refactor server (cause it's large)
# 3. Refactor clock (cause it's weird)