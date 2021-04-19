

from mido import MidiFile
import argparse
parser = argparse.ArgumentParser()

# mid = MidiFile('output/song.mid')

parser.add_argument('--file', type=str)

args = parser.parse_args()

if args.file is None:
  print("No file provided")
  exit(1)


mid = MidiFile(args.file)

for i, track in enumerate(mid.tracks):
  print('Track {}: {}'.format(i, track.name))
  print(f'ticks_per_beat: {mid.ticks_per_beat}')
  for msg in track:
      print(msg)

# for i in range(0,10):
#   try:
#       mid = MidiFile(f'output/guess-promptname-{i}.mid')
# 
#       for i, track in enumerate(mid.tracks):
#         print('Track {}: {}'.format(i, track.name))
#         for msg in track:
#             print(msg)
#   except:
#     pass