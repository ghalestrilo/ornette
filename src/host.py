from bridge import Bridge
from clock import Clock

import pprint
import mido
import data

state = {
    # Basic Config
    'module': None,
    'model': None, # Deprecate
    'scclient': None,
    'debug_output': True,
    'sync_mode': False, # Deprecate

    'temperature': 1.2,
    'until_next_event': 0.25,

    # Controls
    'buffer_length': 64,
    'trigger_generate': 0.5,

    # Operation/Playback Variables
    'is_running': False,
    'is_generating': False,
    'playback': True,
    'playhead': 0,
    'history': [[]],
    'output_data': [],
    'return': 0,
    'tempo': 120,
    'time_shift_denominator': 100,
    'save_output': True,

    # Batch execution control
    'batch_mode': False,
    # 'batch_max_buffer': False,
    'data_frame': None,
}

class Host:
    def __init__(self,args):
      self.state = state
      init_state(args)
      self.bridge = Bridge(self,args)
      self.model = data.load_model(self,args.checkpoint)
      self.clock = Clock(self)
      pass

    def start(self):
      self.clock.start()
      self.bridge.start()
      # TODO: Try moving this to close
      self.clock.stop()
      self.model.close()

    def set(self,field,value):
      try:
        state[field] = value
        print("[{0}] ~ {1}".format(field, value))
      except KeyError:
          print("no such key ~ {0}".format(field))
          pass
    
    def print(self, field=None, pretty=True):
      """ Print a key from the host state """
      if (field == None):
        pprint.pprint(state)
        return
      try:
          data = state[field]
          print("[{0}] ~ {1}".format(field, data))
          if (pretty == True and field == 'history'):
            pprint.pprint([self.model.decode(e) for e in data[0]])
            return
          if (pretty == True and field == 'output_data'):
            pprint.pprint(data)
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

      # Generate sequence
      seq = self.model.tick()[-max_seq:]

      # (Batch Mode) Notify maximum requested length has been met
      if (state['batch_mode']):
        if (len(seq) == max_seq):
            self.notify_task_complete()

      # Maybe create Host#rewind
      new_playhead = max(playhead - buflen + (len(seq) - len(hist)), 0)
      if (self.is_debugging()):
          print(f'Rewinding Playhead ({playhead} -> {new_playhead})')

      self.state['playhead'] = new_playhead
      state['history'][0] = seq
      
      state['is_generating'] = False
      self.clock.notify_wait(False)
      if (self.is_debugging()):
          print('history: {}'.format([self.model.decode(h) for h in hist]))



    
    # Query Methods
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
      return self.peek(0)

    def peek(self,offset=1):
      """ Check next event in history """
      hist = self.state['history']
      playhead = self.state['playhead']

      if (self.has_history() == False): return None

      # FIXME: I think this is not being called
      if (playhead >= len(hist[0])): self.clock.notify_wait()

      position = playhead + offset

      if (position >= len(hist[0])): return None

      if (position < 0):
        print(f'Warning: trying to read a negative position in history ({playhead} + {offset} = {position})')
        return None

      return hist[0][position]
    
    # Playback Methods
    def get_action(self,message):
        ''' Get Action
            Decode a midi message into a sequence of actions
        '''
        # TODO: use mido.tick2second() to convert time
        name, note, velocity, time = message
        msg = mido.Message(name,
          note=note,
          velocity=velocity,
          time=int(time * 4 * state['tempo']))
          
        data.add_message(state, msg)
        return [('wait', time), ('play', note)]

    def perform(self,action):
      ''' Performs a musical action described by a tuple (name, value)
          Name can be:
          
          'wait': waits value miliseconds until next action is performed
          'play': sends an osc message to play the desired note (value)
      '''
      name, value = action
      if (self.is_debugging()):
        print(f'({state["playhead"]}/{len(state["history"][0])}): {name} {value}')

      if (state['batch_mode']): return

      if (name == 'play'): self.play(int(value))
      if (name == 'wait'): state['until_next_event'] = value

    def process_next_token(self):
      ''' Reads the next token from the history
          Decodes the token onto a mido messagee
          Saves the message to the output
          Decodes each message into actions
          Performs the required actions
          Increments playhead
      '''
      e = self.get_next_token()

      if (e == None):
        print("No event / history is empty")
        return

      for message in self.model.decode(e):
        for action in self.get_action(message):
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

    def reset(self):
        [voice.clear() for voice in state['history']]
        state['playhead'] = 0
        state['output_data'].clear()

    # Data Methods
    def load_midi(self, name):
        data.load_midi(self, name)

    def save_output(self, name):
        data.save_output(name, state['output_data'])

    # Batch Mode Methods
    def notify_task_complete(self):
        self.bridge.notify_task_complete()

    # Analysis Methods
    def get_decoded_history(self):
        return []

    def get_bars(self):
        return []

#     def debug_tensorflow():
#       tf.config.list_physical_devices("GPU")
#       print('tf.test.is_gpu_available() = {}'.format(tf.test.is_gpu_available()))

def init_state(args):
    state['module'] = args.module
    state['playback'] = args.playback
    state['max_seq'] = args.max_seq
    state['output'] = None
    state['batch_mode'] = args.batch_mode
    # state['history'] = [[int(x) for x in str(args.state).split(',')]]
