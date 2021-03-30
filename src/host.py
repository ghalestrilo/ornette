from bridge import Bridge
from clock import Clock
from module_interface import load_model
import pprint

state = {
    'is_running': False,
    'is_generating': False,
    'history': [[]],
    'temperature': 1.2,
    'until_next_event': 0.25,
    'buffer_length': 64,
    'trigger_generate': 0.5,
    'playback': True,
    'playhead': 0,
    'module': None,
    'model': None,
    'scclient': None,
    'debug_output': True,
    'sync_mode': False,
    'return': 0,
    'tempo': 120,
    'time_shift_denominator': 100,
}

class Host:
    def __init__(self,args):
      self.state = state
      init_state(args)
      self.bridge = Bridge(self,args)
      self.model = load_model(state,args.checkpoint)
      self.clock = Clock(self)
      pass

    def start(self):
      self.clock.start()
      self.bridge.start()
      # TODO: Try moving this to close
      self.clock.stop()
      self.model.close()

    # FIXME: May be reserved
    def set(self,field,value):
      try:
        state[field] = value
        print("[{0}] ~ {1}".format(field, value))
      except KeyError:
          print("no such key ~ {0}".format(field))
          pass
    
    def print(self, args=None, pretty=True):
      field = args
      if (args == None):
        pprint.pprint(state)
        return
      try:
          # data = [state['model'].word2event[word] for word in state[field][0]] if field == 'history' else state[field]
          data = state[field]
          if (pretty == True and field == 'history'):
            pprint.pprint([self.model.decode(e) for e in data[0]])
            return
          print("[{0}] ~ {1}".format(field, data))
      except KeyError:
          print("no such key ~ {0}".format(field))
          pass

    def close(self):
        self.clock.stop()
        self.bridge.stop()

    def play(self,pitch,instr=None):
      if (instr == None): self.bridge.play(pitch)
      else: self.bridge.play(pitch, instr)

    
    # TODO: Bug here - playhead will not rewind
    def generate(self):
      state['is_generating'] = True
      hist = self.state['history'][0]
      threshold = self.state['trigger_generate']
      playhead = self.state['playhead']

      max_seq = self.state['buffer_length'] 

      buflen = self.state['buffer_length']

      if (self.is_debugging()):
          print("Generating more tokens ({} /{} > {})".format(playhead, len(hist), threshold))

      seq = self.model.tick()[-max_seq:]

      # Maybe create Host#rewind
      new_playhead = max(playhead - buflen + (len(seq) - len(hist)), 0)
      if (self.is_debugging()):
          print(f'Rewinding Playhead ({playhead} -> {new_playhead})')

      self.state['playhead'] = new_playhead
      state['history'][0] = seq
      
      state['is_generating'] = False
      if (self.is_debugging()):
          print('history: {}'.format([self.model.decode(h) for h in hist]))

    

    def has_history(self):
      hist = self.state['history']
      # return np.any(hist) and np.any(hist[0])
      return any(hist) and any(hist[0])

    def must_generate(self):
      if (state['is_generating'] == True): return False
      elif (self.has_history() == False): return True
      return self.state['playhead'] / len(self.state['history'][0]) > self.state['trigger_generate']

    def is_debugging(self):
      return self.state['debug_output'] == True

    def get_next_token(self):
      hist = self.state['history']

      if (self.has_history() == False):
        return None

      if (self.state['playhead'] >= len(hist[0])):
        self.wait_for_more = True
        return None

      # return self.host.model.decode(self.state['history'][0][self.state['playhead']])
      return self.state['history'][0][self.state['playhead']]

    def perform(self,action):
        name, value = action
        if (name == 'play'): self.play(int(value))
        if (name == 'wait'): state['until_next_event'] = value

    def process_next_token(self):
      e = self.get_next_token()

      if (e == None):
        print("No event / history is empty")
        return

      actions = self.model.get_action(e)
      if (actions is None):
          print(f'No action returned for event {e}')
          return
      
      for action in actions:
        self.perform(action)

      self.state['playhead'] = self.state['playhead'] + 1

    # TODO: Do I need this?
    def is_running(self):
      return state['is_running']

    def clock_running(self):
      return state['clock_running']

    def push_event(self,event):
        print("[event] ~ {0}".format(event))
        state['history'][0].append(event)
    # /TODO

# def sample_model(, args):
#     model = args[0]
#     event = model.predict()
#     print(event)


def server_reset():
    [voice.clear() for voice in state['history']]
    state['playhead'] = 0

# def debug_tensorflow():
#   tf.config.list_physical_devices("GPU")
#   print('tf.test.is_gpu_available() = {}'.format(tf.test.is_gpu_available()))

def init_state(args):
    state['module'] = args.module
    state['playback'] = args.playback
    state['max_seq'] = args.max_seq
    # state['history'] = [[int(x) for x in str(args.state).split(',')]]
