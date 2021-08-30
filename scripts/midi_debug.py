

from mido import MidiFile
import argparse
parser = argparse.ArgumentParser()

# mid = MidiFile('output/song.mid')

parser.add_argument('--file', type=str)

args = parser.parse_args()

if args.file is None:
  print("No file provided")
  exit(1)

print(args.file)
mid = MidiFile(args.file)
timesig = [msg for msg in mid if msg.type == 'time_signature']
timesig = timesig[0].denominator if any(timesig) else 4

total_ticks = [sum(msg.time for msg in track) for track in mid.tracks]
total_ticks = max(total_ticks)
total_beats = total_ticks / mid.ticks_per_beat
total_bars = total_beats / timesig

print(f'Length: {total_ticks} ticks = {total_beats} beats = {total_bars} bars')
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