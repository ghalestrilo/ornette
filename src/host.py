from bridge import Bridge
from clock import Clock

import pprint
import mido
import data
from os import environ

state = {
    # Basic Config
    'module': None,
    'scclient': None,
    'debug_output': True,

    'temperature': 1.2,
    'until_next_event': 0.25,

    # Controls
    'buffer_length': 64,     # read from .ornette.yml
    'trigger_generate': 0.5, # read from .ornette.yml

    # Operation/Playback Variables
    'history': [[]],
    'is_running': False,
    'is_generating': False,
    'playback': True,
    'playhead': 0,
    'return': 0,
    'time_shift_denominator': 100,
    'missing_beats': 4,  # How many beats should the generator generate?
    'input_unit': 'beats',
    'output_unit': 'beats',
    'instrument': [ 's', 'superpiano' ],
    'last_end_time': 0,
    # 'instrument': [ 's', 'mc', 'midichan', 0 ],

    # MIDI  Output fields
    'output_data': [],
    'save_output': True,
    'track_name': 'Acoustic Grand Piano',
    'bpm': 120,
    'midi_tempo': None,
    'time_signature_numerator': 4, 
    'time_signature_denominator': 4,
    'ticks_per_beat': 960, # TODO: How do I determine that?
    'steps_per_quarter': 8,

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

      # Notify startup for batch runner
      pass

    def start(self):
      try:
        self.reset()
        self.clock.start()
        if (self.state['batch_mode']): self.notify_task_complete()
        self.bridge.start()
      except KeyboardInterrupt:
          self.close()
          return
      self.close()

    def set(self,field,value):
      try:
        state[field] = value
        print("[{0}] ~ {1}".format(field, value))
      except KeyError:
          print(f'no such key ~ {field}')
          pass
    
    def get(self,field):
      try:
        return state[field]
      except KeyError:
          print(f'no such key ~ {field}')
          pass

    def print(self, field=None, pretty=True):
      """ Print a key from the host state """
      
      if (field == None):
        pprint.pprint(state)
        return
      try:
          if (field == 'time'):
            self.time_debug()
            return

          data = state[field]
          if (pretty == True and field == 'history'):
            for voice in data:
              pprint.pprint([self.model.decode(e) for e in voice])
            print(f'{len(data)} voices total')
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
        self.model.close()
        self.bridge.stop()

    def play(self,pitch,instr=None):
      if (instr == None): self.bridge.play(pitch)
      else: self.bridge.play(pitch, instr)

    def generate(self, length=state['missing_beats'], unit='beats', respond=False):
      state['is_generating'] = True
      hist = self.state['history'][0]
      threshold = self.state['trigger_generate']
      playhead = self.state['playhead']

      max_len = self.state['buffer_length'] 

      if (self.is_debugging()):
          print(f'[server] generating tokens ({playhead}/{len(hist)} > {threshold})')
          print(f'[server] requested length: {length} {unit} ({self.to_ticks(length, unit)} ticks)')

      # Generate sequence
      ticks = self.to_ticks(length, unit)
      final_length = self.from_ticks(ticks, state['input_unit'])
      seq = self.model.generate(state['history'], final_length)

      # # (Batch Mode) Notify maximum requested length has been met
      # if (state['batch_mode'] and len(seq) >= max_len):
      #     self.notify_task_complete()

      # Update Playhead
      self.rewind(max(0, len(seq) - max_len))

      state['history'][0] = seq[-max_len:]
      
      state['is_generating'] = False
      self.clock.notify_wait(False)
      # if (self.is_debugging()):
      #     print('history: {}'.format([self.model.decode(h) for h in hist]))

      if (respond):
        self.dump_history()
        self.notify_task_complete()

    def rewind(self, number):
      playhead = self.state['playhead']
      target_playhead = playhead - number
      new_playhead = max(target_playhead, 0)
      if (self.is_debugging()):
          # print(f' max_len: {max_len} | generator_overflow: {generator_overflow} | len(seq): {len(seq)} | len(hist): {len(hist)}')
          # print(f' target playhead: {target_playhead}')
          print(f'Rewinding Playhead ({playhead} -> {new_playhead})')

      self.state['playhead'] = new_playhead

    
    # Query Methods
    def has_history(self):
      hist = self.state['history']
      # return np.any(hist) and np.any(hist[0])
      return any(hist) and any(hist[0]) and (len(hist[0]) > 0)

    def task_ended(self):
      # if len(state['history']) == 0 or len(state['history'][0]): return False
      did_it_end = len(state['history'][0]) >= state['buffer_length']
      # if (did_it_end): self.notify_task_complete()
      return did_it_end

    def must_generate(self):
      if (state['is_generating'] == True): return False
      elif (self.has_history() == False): return True
      # print(f'{self.state["playhead"]} / {len(self.state["history"][0])} >= {self.state["trigger_generate"]}')
      if (state['batch_mode'] and self.task_ended()): return False
      return self.state['playhead'] / len(self.state['history'][0]) >= self.state['trigger_generate']

    def is_debugging(self):
      return self.state['debug_output'] == True

    def get_next_token(self):
      return self.peek(0)

    def peek(self,offset=1):
      """ Check next event in history """
      hist = self.state['history']
      playhead = self.state['playhead']

      if (self.has_history() == False): return None

      no_more_tokens = playhead >= len(hist[0])
      position = playhead + offset

      if (no_more_tokens):
          self.clock.notify_wait()
          return None

      if (position < 0):
        print(f'Warning: trying to read a negative position in history ({playhead} + {offset} = {position})')
        return None

      return hist[0][position]
    
    # Playback Methods
    def get_action(self,message):
        ''' Get Action
            Decode a midi message into a sequence of actions
        '''
        name, note, velocity, time = message
        msg = mido.Message(name,
          note=note,
          channel=1,
          velocity=velocity,
          time=int(round(mido.second2tick(time, state['ticks_per_beat'], state['midi_tempo'])))) 
          
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

      if (state['batch_mode']):
        state['until_next_event'] = 0
        return

      if (name == 'play'): self.play(int(value))
      
      # FIXME: Calculate seconds from incoming value unit (melody_rnn: beats)
      if (name == 'wait'):
          # ticks = self.to_ticks(value, state['output_unit'])
          # secs = self.from_ticks(ticks, 'seconds')
          state['until_next_event'] = value
      

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
        if (self.is_debugging()): print("No event / history is empty")
        if (state['batch_mode'] and self.task_ended()):
            self.set('is_running', False)
            self.save_output(state['output_filename'])
        return

      for message in self.model.decode(e):
        for action in self.get_action(message):
          self.perform(action)

      self.state['playhead'] = self.state['playhead'] + 1

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
        self.set('playhead', 0)
        self.set('last_end_time', 0)
        if state['midi_tempo'] is None: state['midi_tempo'] = mido.bpm2tempo(state['bpm'])
        data.init_output_data(state)
        self.clock.notify_wait(False)

    def load_midi(self, name, barcount=None):
        data.load_midi(self, name, barcount, 'bars')

        self.print('history')

    def save_output(self, name):
        data.save_output(name, state['output_data'], state['ticks_per_beat'], self)

    # Batch Mode Methods
    def notify_task_complete(self):
        self.bridge.notify_task_complete()

    def get_instrument(self):
        return state['instrument']

#     def debug_tensorflow():
#       tf.config.list_physical_devices("GPU")
#       print('tf.test.is_gpu_available() = {}'.format(tf.test.is_gpu_available()))








    # def steps_to_seconds(self,steps):
    #     return (state['ticks_per_beat'] * steps
    #       / state['bpm']
    #       / state['steps_per_quarter'])

    def get_measure_length(self, unit):
        length = 1
        if (unit == 'measures'): return length
        return self.get_beat_length(length, unit)

    def get_beat_length(self, length, unit):
        length = length * 4 * state['time_signature_numerator'] / state['time_signature_denominator']
        if (unit == 'beats'): return length

        length = length * state['ticks_per_beat']
        if (unit == 'ticks'): return length
        
        if (unit == 'seconds'):
          return mido.tick2second(length,
            state['ticks_per_beat'],
            state['midi_tempo'])
        return None

    def from_ticks(self, length, unit):
        if (length is None): return None
        if (unit == 'ticks'): return length

        if (unit == 'seconds'):
          return mido.tick2second(length,
            state['ticks_per_beat'],
            state['midi_tempo'])

        length = length / state['ticks_per_beat']
        if (unit == 'beats'):
          return length

        length = length / (4 * state['time_signature_numerator'] / state['time_signature_denominator'])
        if (unit in ['measures', 'bars']): 
          return length

        return None

    def to_ticks(self, length, unit):
        if (length is None): return None
        if (unit == 'seconds'): return mido.second2tick(length, state['ticks_per_beat'], state['midi_tempo'])

        if (unit == 'ticks'): return length

        length = length * state['ticks_per_beat']
        if (unit == 'beats'): return length

        length = length * 4 * state['time_signature_numerator'] / state['time_signature_denominator']
        if (unit in ['measures', 'bars']): return length
        return None

    def ticks_per_token(self):
      return sum([0 for x in state['history']]) / len(state['history']) if self.has_history() else None

    def time_debug(self, measures=1):
      # beats = self.get_measure_length('beats')
      # ticks = self.get_measure_length('ticks')
      # seconds = self.get_measure_length('seconds')
      # tokens = self.get_measure_length('tokens')
      ticks = self.to_ticks(measures, 'measures')
      beats = self.from_ticks(ticks, 'beats')
      ticks = self.from_ticks(ticks, 'ticks')
      seconds = self.from_ticks(ticks, 'seconds')
      tokens = self.from_ticks(ticks, 'tokens')
      tempo = state['midi_tempo']
      bpm = state['bpm']
      tpb = state['ticks_per_beat']
      gtf = self.to_ticks
      print('[server] Time info:')
      print(f'   {measures} measure = {beats} beats = {ticks} ticks = {seconds} seconds ~ {tokens} tokens')
      print(f'   {gtf(1, "measures")} == {gtf(beats, "beats")} == {gtf(ticks, "ticks")} == {gtf(seconds, "seconds")} ~ {gtf(tokens, "tokens")}')
      print(f'   tempo: {tempo} | bpm: {bpm} | tpb: {tpb}')
      print(f'   missing beats: {state["missing_beats"]} | unit: {state["input_unit"]}')

    # Analysis Methods
    def get_decoded_history(self):
        return []

    def dump_history(self):
      for e in state['history'][0]:
          for message in self.model.decode(e):
            self.get_action(message)

    def get_bars(self):
        return []



def init_state(args):
    state['module'] = args.module
    state['playback'] = args.playback
    state['max_seq'] = args.max_seq
    state['output'] = None
    state['batch_mode'] = args.batch_mode
    # state['history'] = [[int(x) for x in str(args.state).split(',')]]
