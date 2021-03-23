import os
import sys

import tensorflow as tf
import numpy as np
# import miditoolkit
# import modules
import pickle
import time
import argparse
import asyncio
import math
import pprint

from threading import Thread, Event
from pythonosc import dispatcher, osc_server, udp_client

# tf.compat.v1.disable_eager_execution()
# tf.compat.v1.disable_eager_execution()

CODE_REBOOT=2222

os.environ['CUDA_VISIBLE_DEVICES'] = '0'

# TODO: Move to engine.py
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
    'time_shift_denominator': 100,
}
NOTE_OFFSET=60

# Clock implements the main loop
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
      return np.any(hist) and np.any(hist[0])

    def get_next_token(self):
      hist = state['history']

      if (self.has_history() == False):
        return None

      if (state['playhead'] >= len(hist[0])):
        self.wait_for_more = True
        return None

      return state['model'].decode(state['history'][0][state['playhead']]) 

    def play_next_token(self):
      e = self.get_next_token()

      if (e == None):
        print("No event / history is empty")
        return

      (event_name, event_value) = e
      if (event_name == 'note_on' or event_name == 'Note On'):    play(int(event_value))
      if (event_name == 'time_shift'): state['until_next_event'] = event_value / state['time_shift_denominator']

      state['playhead'] = state['playhead'] + 1


    def run(self):
      model = state['model']

      self.generate_in_background()
      while not self.stopped.wait(state['until_next_event']):
        if (state['is_running'] == True and self.wait_for_more == False):
          self.play_next_token()

          if(len(state['history'][0]) == 0):
            self.generate_in_background()
            return

          if (state['playhead'] / len(state['history'][0]) > state['trigger_generate']):
            if (state['debug_output'] == True):
              print("Generating more tokens ({} /{} > {})".format(state['playhead'], len(state['history'][0]), state['trigger_generate']))            
            self.generate_in_background()

            if (state['debug_output'] == True):
              print('history: {}'.format([model.decode(h) for h in state['history'][0]]))


def start_timer():
    stopFlag = Event()
    state['stopFlag'] = stopFlag
    state['clock'] = Clock(stopFlag)
    state['clock'].start()


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
        print("[{0}] ~ {1}".format(field, data))
    except KeyError:
        print("no such key ~ {0}".format(field))
        pass


def sample_model(unused_addr, args):
    model = args[0]
    event = model.predict()
    print(event)

def prepare_model(unused_addr, args):
    model = args[0]
    event = model.realtime_setup(state)
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
        dispatcher.map("/prep",   prepare_model, model)
    
    if (state['playback'] == True):
      dispatcher.map("/play", lambda _,note: play(note))

def load_folder(name):
  sys.path.append(os.path.join(sys.path[0], name))

def load_model():
  model_name = state['model_name']
  model_path = os.path.join('models', model_name)
  load_folder(model_path)
  from ornette import OrnetteModule
  return OrnetteModule(state, checkpoint=os.path.join(model_path,'REMI-tempo-checkpoint'))
  print("Unkown model: " + str(state['model_name'] + ". Aborting load..."))
  exit(-1)

# /TODO: Move to engine.py

# Main
if __name__ == "__main__":
    
    # Parse CLI Args
    parser = argparse.ArgumentParser()

    # TODO: These can all be constructed from a dictionary inside the 
    # If any of the args are present, then pass them to the server, or just pass all default values
    parser.add_argument('--max_seq', default=256, help='maximum buffer length', type=int)

    parser.add_argument('--state', default="0", help='the initial state of the improv', type=str)
    parser.add_argument("--ip", default="127.0.0.1", help="The ip to listen on")
    parser.add_argument("--port", type=int, default=5005, help="The port to listen on")

    parser.add_argument("--model_name", type=str,  default="MusicTransformer-tensorflow2.0", help="The model to use (music-transformer, remi)")
    parser.add_argument("--playback",   type=bool, default=True, help="Use supercollider for sound playback")
    parser.add_argument("--sc-ip",      type=str,  default="127.0.0.1", help="The supercollider server ip")
    parser.add_argument("--sc-port",    type=int,  default=57120, help="The supercollider server ip")

    args = parser.parse_args()

    state['model_name'] = args.model_name
    state['playback'] = args.playback
    state['scclient'] = udp_client.SimpleUDPClient(args.sc_ip, args.sc_port)
    state['max_seq'] = args.max_seq
    state['history'] = [[int(x) for x in str(args.state).split(',')]]


    # Prep Model
    model = load_model()
    prepare_model(None, [model])  # for real time use

    # Prep Server
    dispatcher = dispatcher.Dispatcher()
    bind_dispatcher(dispatcher, model)

    # print(tf.compat.v1.get_default_graph(model))

    # Start Server
    state['server'] = osc_server.ThreadingOSCUDPServer((args.ip, args.port), dispatcher)
    print("Serving {} on {}".format(state['model_name'], state['server'].server_address))
    start_timer()
    state['server'].serve_forever()
    stop_timer()

    #Cleanup
    model.close()
    if (state['return']==CODE_REBOOT):
      print("Should Reboot")
    state['return']