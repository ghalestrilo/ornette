import os
import sys

# Move to utils.py?
def load_folder(name):
  sys.path.append(os.path.join(sys.path[0], name))

load_folder('src')

import tensorflow as tf
import numpy as np
# import miditoolkit
# import modules
import pickle
import time
#import asyncio
import math
import pprint

from args import get_args

from threading import Thread, Event
from pythonosc import dispatcher, osc_server, udp_client
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
NOTE_OFFSET=60

os.environ['CUDA_VISIBLE_DEVICES'] = '0'

# TODO: Move to server.py
state = {
    'is_running': False,
    'is_generating': False,
    'history': [[]],
    'temperature': 1.2,
    'until_next_event': 0.25,
    'buffer_length': 16,
    'trigger_generate': 0.5,
    'playback': True,
    'playhead': 0,
    'model_name': None,
    'model': None,
    'scclient': None,
    'debug_output': False,
    'sync_mode': False,
    'return': 0,
    'tempo': 120,
    'time_shift_denominator': 100,
}

# TODO: Move to playback.py
class Clock(Thread):
    def __init__(self, event):
      Thread.__init__(self)
      self.stopped = event
      state['playhead'] = 0
      self.wait_for_more = False

    
    def generate(self):
      seq = state['model'].tick()[-128:]
      state['playhead'] = state['playhead'] - state['buffer_length'] + (len(seq) - len(state['history'][0]))
      state['playhead'] = max(state['playhead'], 0)
      state['history'][0] = seq
      self.wait_for_more = False

    def generate_in_background(self):
      Thread(target=self.generate).start()

    def has_history(self):
      hist = state['history']
      # return np.any(hist) and np.any(hist[0])
      return any(hist) and any(hist[0])

    def get_next_token(self):
      hist = state['history']

      if (self.has_history() == False):
        return None

      if (state['playhead'] >= len(hist[0])):
        self.wait_for_more = True
        return None

      # return state['model'].decode(state['history'][0][state['playhead']])
      return state['history'][0][state['playhead']]

    def process_next_token(self):
      e = self.get_next_token()

      if (e == None):
        print("No event / history is empty")
        return

      action = state['model'].get_action(e)
      if (action is None):
          print(f'No action returned for event {e}')
          return

      for (name, value) in action:
        if (name == 'play'): play(int(value))
        if (name == 'wait'): state['until_next_event'] = value

      state['playhead'] = state['playhead'] + 1


    def run(self):
      model = state['model']

      self.generate_in_background()
      while not self.stopped.wait(state['until_next_event']):
        if (state['is_running'] == True and self.wait_for_more == False):
          self.process_next_token()

          if(len(state['history'][0]) == 0):
            self.generate_in_background()
            return

          if (state['playhead'] / len(state['history'][0]) > state['trigger_generate']):
            if (state['debug_output'] == True):
              print("Generating more tokens ({} /{} > {})".format(state['playhead'], len(state['history'][0]), state['trigger_generate']))            
            self.generate_in_background()

            if (state['debug_output'] == True):
              print('history: {}'.format([model.decode(h) for h in state['history'][0]]))


# Make this into a constructor
def start_timer():
    stopFlag = Event()
    state['stopFlag'] = stopFlag
    state['clock'] = Clock(stopFlag)
    state['clock'].start()

# TODO: Move to playback.py



def stop_timer():
    # this will stop the timer
    state['stopFlag'].set()

def engine_set(unused_addr, args):
    try:
        field, value = args
        state[field] = value
        print("[{0}] ~ {1}".format(field, value))
    except KeyError:
        print("no such key ~ {0}".format(field))
        pass


def push_event(unused_addr, event):
    print("[event] ~ {0}".format(event))
    state['history'][0].append(event)


def engine_print(unused_addr, args=None):
    field = args
    if (args == None):
      pprint.pprint(state)
      return
    try:
        # data = [state['model'].word2event[word] for word in state[field][0]] if field == 'history' else state[field]
        data = state[field]
        if (field == 'history'):
          pprint.pprint([state['model'].decode(e) for e in data[0]])
          return
        print("[{0}] ~ {1}".format(field, data))
    except KeyError:
        print("no such key ~ {0}".format(field))
        pass


def sample_model(unused_addr, args):
    model = args[0]
    event = model.predict()
    print(event)

def play(note):
    state['scclient'].send_message('/play2', ['s', 'superpiano', 'note', note - NOTE_OFFSET])

def shutdown(unused_addr):
    stop_timer()
    state['server'].shutdown()

def server_reset(unused_addr):
    [voice.clear() for voice in state['history']]
    state['playhead'] = 0

def server_reboot(unused_addr):
    shutdown(None)
    state['return'] = CODE_REBOOT

def debug_tensorflow(unused_addr):
  tf.config.list_physical_devices("GPU")
  print('tf.test.is_gpu_available() = {}'.format(tf.test.is_gpu_available()))

def bind_dispatcher(dispatcher, model):
    state['model'] = model
    dispatcher.map("/start", engine_set, 'is_running', True)
    dispatcher.map("/pause", engine_set, 'is_running', False)
    dispatcher.map("/reset", server_reset)
    dispatcher.map("/reboot", server_reboot)  # event2word
    dispatcher.map("/end", shutdown)
    dispatcher.map("/quit", shutdown)
    dispatcher.map("/exit", shutdown)
    dispatcher.map("/debug", engine_print)
    dispatcher.map("/tfdebug", debug_tensorflow)
    dispatcher.map("/event", push_event)  # event2word

    dispatcher.map("/set", lambda addr, k, v: engine_set(addr, [k, v]))

    if (model):
        dispatcher.map("/sample", sample_model, model)
    
    if (state['playback'] == True):
      dispatcher.map("/play", lambda _,note: play(note))

def load_model(checkpoint=None):
  if checkpoint is None:
    print("Please provide a checkpoint for the model to load")
    exit(-1)

  # model_name = state['model_name']
  # model_path = os.path.join('modules', model_name)
  model_path = '/model'
  load_folder(model_path)
  from ornette import OrnetteModule
  return OrnetteModule(state, checkpoint=checkpoint)
  print("Unkown model: " + str(state['model_name'] + ". Aborting load..."))
  exit(-1)

def init_state(args):
    state['model_name'] = args.model_name
    state['playback'] = args.playback
    state['scclient'] = udp_client.SimpleUDPClient(args.sc_ip, args.sc_port)
    state['max_seq'] = args.max_seq
    state['history'] = [[int(x) for x in str(args.state).split(',')]]

# /TODO: Move to server.py



# TODO: Move to init.py
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
# /TODO







# Main
if __name__ == "__main__":
    args = get_args()

    prep_module()

    # Parse Args (import from args.py)
    # args = args

    # Prep Model
    model = load_model(args.checkpoint)

    # Prep Server
    # server = server(model, args)
    dispatcher = dispatcher.Dispatcher()
    bind_dispatcher(dispatcher, model)

    # Start Server
    state['server'] = osc_server.ThreadingOSCUDPServer((args.ip, args.port), dispatcher)
    print("Serving {} on {}".format(state['model_name'], state['server'].server_address))
    
    # TODO: Change into 
    # timer = Timer(server)
    # timer.start()
    start_timer()
    state['server'].serve_forever()
    stop_timer()

    # Timer.close()

    # Cleanup
    model.close()
    if (state['return']==CODE_REBOOT):
      print("Should Reboot")
    state['return']



## Steps to refactor

# 1. Refactor args (cause it's easy)
# 2. Refactor server (cause it's large)
# 3. Refactor clock (cause it's weird)