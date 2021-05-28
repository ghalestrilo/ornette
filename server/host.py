from bridge import Bridge
from engine import Engine
from song import Song
from logger import Logger
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
    'save_output': True, # depr
    'track_name': 'Acoustic Grand Piano', # depr
    'bpm': 120, # 
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
      self.io = Logger(self)
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
        if (self.state['batch_mode']): self.bridge.notify_task_complete()
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

    # Host, Song, Engine
    def reset(self):
        [voice.clear() for voice in state['history']]
        self.set('playhead', 0)
        self.set('last_end_time', 0)
        if state['midi_tempo'] is None: state['midi_tempo'] = mido.bpm2tempo(state['bpm'])
        self.song.init_output_data(state,conductor=False) # .reset
        self.engine.notify_wait(False)





















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
            self.io.log(f'output_data: {self.get("output_data")}')
          
        state[field] = value
        if silent or field == 'last_end_time': return
        self.io.log("[{0}] ~ {1}".format(field, value))
      except KeyError:
          if not silent: self.io.log(f'no such key ~ {field}')
          pass
    
    def get(self,field):
      try:
        return state[field]
      except KeyError:
          self.io.log(f'no such key ~ {field}')
          pass

    # /TODO: State



















    # Batch (depr)
    def task_ended(self):
      # if len(state['history']) == 0 or len(state['history'][0]): return False
      did_it_end = len(self.song.get_voice()) >= state['buffer_length']
      # if (did_it_end): self.notify_task_complete()
      return did_it_end


#     def debug_tensorflow():
#       tf.config.list_physical_devices("GPU")
#       self.io.log('tf.test.is_gpu_available() = {}'.format(tf.test.is_gpu_available()))





# TODO: State
def init_state(args):
    state['module'] = args.module
    state['playback'] = args.playback
    state['max_seq'] = args.max_seq
    state['output'] = None
    state['batch_mode'] = args.batch_mode
    # state['history'] = [[int(x) for x in str(args.state).split(',')]]
