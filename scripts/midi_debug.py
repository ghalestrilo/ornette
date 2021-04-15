

from mido import MidiFile

# mid = MidiFile('output/song.mid')

for i in range(0,10):
  try:
      mid = MidiFile(f'output/guess-promptname-{i}.mid')

      for i, track in enumerate(mid.tracks):
        print('Track {}: {}'.format(i, track.name))
        for msg in track:
            print(msg)
  except:
    pass