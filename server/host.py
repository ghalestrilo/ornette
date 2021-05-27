from bridge import Bridge
from engine import Engine
from song import Song

import pprint
import mido
import data
from os import environ



# TODO: State
state = {
    # Basic Config
    'module': None,
    'scclient': None,
    'debug_output': True,

    'until_next_event': 0.25, # TODO: Remove after MIDI-based refactor

    # Controls
    'temperature': 1.2,      # read from .ornette.yml
    'buffer_length': 64,     # read from .ornette.yml
    'trigger_generate': 0.5, # read from .ornette.yml

    # TODO: Move to Engine (Operation/Playback Variables)
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
    'last_end_time': 0,

    # TODO: move to channel
    'voices': [1],
    'instrument': [ 's', 'superpiano', 'velocity', '0.4' ], 

    # TODO: move to track
    'output_data': mido.MidiFile(),
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
    'data_frame': None, # TODO: Remove
}
# /TODO: State

class Host:
    def __init__(self,args):
      self.state = state
      self.data = data
      self.song = Song(self)
      init_state(args)
      self.bridge = Bridge(self,args)
      self.engine = Engine(self)
      self.reset()
      self.set('voices', [1])
      self.model = data.load_model(self,args.checkpoint)

      # Notify startup for batch runner
      pass

    def start(self):
      try:
        self.engine.start()
        if (self.state['batch_mode']): self.notify_task_complete()
        self.bridge.start()
      except KeyboardInterrupt:
          self.close()
          return
      self.close()

    def close(self):
        self.engine.stop()
        self.model.close()
        self.bridge.stop()

    def play(self,pitch,instr=None):
      if (instr == None): self.bridge.play(pitch)
      else: self.bridge.play(pitch, instr)







    # TODO: State
    def set(self,field,value,silent=False):
      try:

        # Move to TrackData
        if (field == 'voices'):
          try: value = list(value)
          except TypeError: value = [value]
          for i in value:
            # print("padding history for")
            while i + 1 > len(self.get('history')): self.set('history', self.get('history') + [[]])
            while i + 1 > len(self.get('output_data').tracks): state['output_data'].tracks.append(mido.MidiTrack())
            self.log(f'output_data: {self.get("output_data")}')
          
        state[field] = value
        if silent or field == 'last_end_time': return
        self.log("[{0}] ~ {1}".format(field, value))
      except KeyError:
          if not silent: self.log(f'no such key ~ {field}')
          pass
    
    def get(self,field):
      try:
        return state[field]
      except KeyError:
          self.log(f'no such key ~ {field}')
          pass

    # /TODO: State



















    # TODO: IO
    def log(self, msg):
      # if self.is_debugging(): print(f"[server] {msg}")
      print(f"[server:{self.get('module')}] {msg}")

    def print(self, field=None, pretty=True):
      """ Print a key from the host state """
      
      if (field == None):
        pprint.pprint(state)
        return
      try:
          if (field == 'time'):
            self.song.time_debug()
            return

          data = state[field]
          if (pretty == True and field == 'history'):
            for voice in data:
              pprint.pprint([self.model.decode(e) for e in voice])
            self.log(f'{len(data)} voices total')
            return
          if (pretty == True and field == 'output_data'):
            pprint.pprint(data)
            return

          self.log("[{0}] ~ {1}".format(field, data))

      except KeyError:
          self.log("no such key ~ {0}".format(field))
          pass
      #/ TODO: IO






    # Query Methods

    def get_voice(self, voice_index=state['voices'][0]):
      print(f'voice_index: {voice_index}')
      return state['history'][voice_index]

    # TODO: get_voice(idx): return self.get('history')[voices[idx]] if idx < len(voices) && voices[idx] < len(self.get('history')) else None
    def has_history(self, voice_id=state['voices'][0]):
      hist = self.get_voice(voice_id)
      # return np.any(hist) and np.any(hist[0])
      print(f'hist({state["voices"][0]}): {True if hist and any(hist) else False}')
      print(hist)
      return True if hist and any(hist) else False

    def task_ended(self):
      # if len(state['history']) == 0 or len(state['history'][0]): return False
      did_it_end = len(self.get_voice()) >= state['buffer_length']
      # if (did_it_end): self.notify_task_complete()
      return did_it_end

    def must_generate(self, voice):
      if (state['is_generating'] == True): return False
      elif (self.has_history(voice) == False): return True
      # print(f'{self.state["playhead"]} / {len(self.state["history"][0])} >= {self.state["trigger_generate"]}')
      if (state['batch_mode'] and self.task_ended()): return False
      return self.state['playhead'] / len(self.get_voice(voice)) >= self.state['trigger_generate']

    def is_debugging(self):
      return self.state['debug_output'] == True

    def get_next_token(self,voice):
      return self.peek(voice,0)

    def peek(self,voice=1,offset=1):
      """ Check next event in history """
      hist = self.state['history']
      playhead = self.state['playhead']

      if (self.has_history() == False): return None

      no_more_tokens = playhead >= len(hist[voice])
      position = playhead + offset

      if (no_more_tokens):
          self.engine.notify_wait()
          return None

      if (position < 0):
        self.log(f'Warning: trying to read a negative position in history ({playhead} + {offset} = {position})')
        return None

      return hist[voice][position]
    
    def decode(self, event, voice):
      return [mido.Message(name,
        note=note,
        channel=voice,
        velocity=velocity,
        time=int(round(mido.second2tick(time, state['ticks_per_beat'], state['midi_tempo']))))
        for (name, note, velocity, time)
        in self.model.decode(event)]

    

    # Playback Methods
    def get_action(self,message,voice=0):
        ''' Get Action
            Decode a midi message into a sequence of actions
        '''
        name, note, velocity, time = message
        msg = mido.Message(name,
          note=note,
          channel=voice,
          velocity=velocity,
          time=self.song.to_ticks(time * self.get('steps_per_quarter'),'beat'))
          
        self.song.add_message(state, msg, voice)
        return [('wait', time), ('play', note)] if name != 'note_off' else [('wait', time)]

    def perform(self,action):
      ''' Performs a musical action described by a tuple (name, value)
          Name can be:
          
          'wait': waits value miliseconds until next action is performed
          'play': sends an osc message to play the desired note (value)
      '''
      name, value = action
      if (self.is_debugging()):
        self.log(f'({state["playhead"]}/{len(state["history"][0])}): {name} {value}')

      if (state['batch_mode']):
        state['until_next_event'] = 0
        return

      if (name == 'play'): self.play(int(value))
      
      # FIXME: Calculate seconds from incoming value unit (melody_rnn: beats)
      if (name == 'wait'):
          # ticks = self.to_ticks(value, state['output_unit'])
          # secs = self.from_ticks(ticks, 'seconds')
          state['until_next_event'] = value
      

    def process_next_token(self, voice=1):
      ''' Reads the next token from the history
          Decodes the token onto a mido messagee
          Saves the message to the output
          Decodes each message into actions
          Performs the required actions
          Increments playhead
      '''
      e = self.get_next_token(voice)

      if (e == None):
        if (self.is_debugging()): self.log(f'No event / voice {voice} is empty')
        if (state['batch_mode'] and self.task_ended()):
            self.set('is_running', False)
            self.save_output(state['output_filename'])
        return

      for message in self.model.decode(e):
        for action in self.get_action(message,voice):
          self.perform(action)

      self.state['playhead'] = self.state['playhead'] + 1


    def reset(self):
        [voice.clear() for voice in state['history']]
        self.set('playhead', 0)
        self.set('last_end_time', 0)
        if state['midi_tempo'] is None: state['midi_tempo'] = mido.bpm2tempo(state['bpm'])
        self.song.init_output_data(state,conductor=False)
        self.engine.notify_wait(False)


    def load_midi(self, name, barcount=None):
        self.log(f' loading {name}')
        self.song.load_midi(self, name, barcount, 'bars')
        if self.get('batch_mode'): self.notify_task_complete()
        if not any(self.get('history')): self.set("history",[[]])
        self.log(f' loaded {sum([len(v) for v in self.get("history")])} tokens to history')

    #/ TODO: Engine




    def is_running(self):
      return state['is_running']

    def engine_running(self):
      return state['engine_running']

    def push_event(self,event,voice=1):
        self.log("[event] ~ {0}".format(event))
        state['history'][voice].append(event)
    # /TODO

    def save_output(self, name):
        data.save_output(name, state['output_data'], state['ticks_per_beat'], self)

    # Batch Mode Methods
    def notify_task_complete(self):
        self.bridge.notify_task_complete()



#     def debug_tensorflow():
#       tf.config.list_physical_devices("GPU")
#       self.log('tf.test.is_gpu_available() = {}'.format(tf.test.is_gpu_available()))








# TODO: State
def init_state(args):
    state['module'] = args.module
    state['playback'] = args.playback
    state['max_seq'] = args.max_seq
    state['output'] = None
    state['batch_mode'] = args.batch_mode
    # state['history'] = [[int(x) for x in str(args.state).split(',')]]
