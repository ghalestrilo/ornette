from mido import MidiTrack

class Channel():
    def __init__(self, index, instrument=None):
        self.index = index
        self.instrument = instrument

        self.user = False
        self.mute = False

    def __eq__(self, other):
      return (self.index == other
              if isinstance(other, int)
              else self.index == other.index)

    # TODO: 
    def play(self, note):
      # [ 'note', pitch - NOTE_OFFSET
      # , 'cut', pitch - NOTE_OFFSET
      # , 'gain', 1
      # ]
      pass