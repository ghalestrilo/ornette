from bridge import Bridge
import pprint

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
    'module': None,
    'model': None,
    'scclient': None,
    'debug_output': False,
    'sync_mode': False,
    'return': 0,
    'tempo': 120,
    'time_shift_denominator': 100,
}

class Host:
    def __init__(self,args):
      self.state = state
      init_state(args)
      self.bridge = Bridge(self)
      pass

    # FIXME: May be reserved
    def set(self,field,value):
      try:
        state[field] = value
        print("[{0}] ~ {1}".format(field, value))
      except KeyError:
          print("no such key ~ {0}".format(field))
          pass
    
    # FIXME: May be reserved
    def print(unused_addr, args=None):
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

    def play(self,pitch):
      self.server.play(pitch)

    # TODO: Do I need this?
    def is_running(self):
      return state['is_running']

    def clock_running(self):
      return state['clock_running']


def push_event(unused_addr, event):
    print("[event] ~ {0}".format(event))
    state['history'][0].append(event)

def sample_model(unused_addr, args):
    model = args[0]
    event = model.predict()
    print(event)


def server_reset(unused_addr):
    [voice.clear() for voice in state['history']]
    state['playhead'] = 0

# def debug_tensorflow(unused_addr):
#   tf.config.list_physical_devices("GPU")
#   print('tf.test.is_gpu_available() = {}'.format(tf.test.is_gpu_available()))

def init_state(args):
    state['module'] = args.module
    state['playback'] = args.playback
    state['scclient'] = 
    state['max_seq'] = args.max_seq
    # state['history'] = [[int(x) for x in str(args.state).split(',')]]
