from mido import MidiTrack

NOTE_OFFSET=60

class Channel():
    def __init__(self, index, instrument=None, host=None):
        self.index = index
        self._instrument = instrument

        self.host = host

        self.user = False
        self.mute = False

    def __eq__(self, other):
      return (self.index == other
              if isinstance(other, int)
              else self.index == other.index)

    def instrument(self):
      return self._instrument

    def set_instrument(self, new_instrument):
      self._instrument = new_instrument

    # TODO: 
    def play(self, message):
      msg = ([ 'note', message.note - NOTE_OFFSET
        , 'cut', message.note
        , 'sustain', 8
        , 'release', 1
        # , 'gain', 0 if message.type == 'note_off' else message.velocity / 127
        , 'gain', 0 if message.type == 'note_off' else message.velocity / 100
        ]
        + self.instrument())
      if self.host is not None: self.host.bridge.play(msg)
      
      # pass