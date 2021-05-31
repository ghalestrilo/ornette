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
      return self._instrument = new_instrument

    # TODO: 
    def play(self, note):
      msg = ([ 'note', note - NOTE_OFFSET
        , 'cut', note - NOTE_OFFSET
        , 'gain', 1
        ]
        + self.instrument())
      if self.host is not None: self.host.bridge.play(msg)
      
      # pass