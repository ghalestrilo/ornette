import mido # FIXME: This is an unnecessary level of coupling

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



class Store():
    def __init__(self, host, args):
      self.host = host
      self.state = state
      state['module'] = args.module
      state['playback'] = args.playback
      state['max_seq'] = args.max_seq
      state['output'] = None
      state['batch_mode'] = args.batch_mode

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
            self.host.io.log(f'output_data: {self.get("output_data")}')
          
        state[field] = value
        if silent or field == 'last_end_time': return
        self.host.io.log("[{0}] ~ {1}".format(field, value))
      except KeyError:
          if not silent: self.host.io.log(f'no such key ~ {field}')
          pass
    
    def get(self,field):
      if field is None: return self.get_state()
      try:
        return state[field]
      except KeyError:
          self.host.io.log(f'no such key ~ {field}')
          pass

    def get_state(self):
      return self.state
