import mido # FIXME: This is an unnecessary level of coupling

state = {
    # Basic Config
    'module': None,
    'scclient': None,
    'debug_output': True,
    'until_next_event': 0.25, # TODO: Remove after MIDI-based refactor

    # Model Parameters
    'temperature': 1.2,             # read from .ornette.yml
    'buffer_length': 64,            # read from .ornette.yml
    'trigger_generate': 0.5,        # read from .ornette.yml
    'is_velocity_sensitive': False, # read from .ornette.yml

    # TODO: Move to Engine (Operation/Playback Variables)
    'is_generating': False, # Keep
    'time_shift_denominator': 100,
    'is_running': False,    # Deprecate?
    'playback': True,       # Deprecate?
    'return': 0,            # Deprecate?
    'history': [[]],        # Deprecate
    'playhead': 0,          # Deprecate
    'missing_beats': 4,     # Deprecate
    'last_end_time': 0,     # Deprecate
    'input_unit': 'beats',  # read from .ornette.yml
    'input_length': 4,      # read from .ornette.yml
    'output_unit': 'beats', # read from .ornette.yml
    'output_length': 4,     # read from .ornette.yml
    'time_coeff': 1,

    # TODO: move to channel
    'output_tracks': [1], # Deprecate
    'instrument': [ 's', 'superpiano', 'velocity', '0.4' ], # Deprecate

    # TODO: move to song
    'output_data': mido.MidiFile(),       # Deprecate
    'save_output': True,                  # Deprecate
    'track_name': 'Acoustic Grand Piano', # Deprecate
    # 'bpm': 120,
    'time_signature_numerator': 4, 
    'time_signature_denominator': 4,
    'tempo': None,
    'ticks_per_beat': 960,
    'pulses_per_quarter': 24,
    'steps_per_quarter': 4,

    # Batch execution control
    'batch_mode': False,
    # 'batch_max_buffer': False,
    'data_frame': None, # TODO: Remove
}



class Store():
    def __init__(self, host, args):
      self.host = host
      self.host.state = state
      self.state = state
      self.state['module'] = args.module
      self.state['playback'] = args.playback
      self.state['max_seq'] = args.max_seq
      self.state['output'] = None
      self.state['batch_mode'] = args.batch_mode

    # TODO: State
    def set(self, field, value, silent=False):
      try:

        if (field in ['bpm', 'qpm']):
          self.host.song.set_qpm(value)


        # Move to TrackData
        if (field == 'output_tracks'):
          try: value = list(value)
          except TypeError: value = [value]
          value = list(map(int,value))
          for i in value:
            while i + 1 > len(self.get('history')): self.set('history', self.get('history') + [[]])
            while i + 1 > len(self.host.song.data.tracks): self.host.song.data.tracks.append(mido.MidiTrack())
            self.host.io.log(f'output_data: {self.get("output_data")}')
          
        self.state[field] = value
        if silent or field == 'last_end_time': return
        self.host.io.log("[{0}] ~ {1}".format(field, value))
      except KeyError:
          if not silent: self.host.io.log(f'no such key ~ {field}')
          pass
    
    def get(self,field):
      if field is None: return self.get_state()
      try:
        return self.state[field]
      except KeyError:
          self.host.io.log(f'no such key ~ {field}')
          pass

    def get_state(self):
      return self.state
