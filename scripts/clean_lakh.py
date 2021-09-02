import mido
import os
import shutil
from tqdm import tqdm
## This script filters the Lakh dataset leaving behind only the melodies it can find
## Output: A set of Two-track MIDI files (conductor + melody)
output_path = "dataset/clean_lahk"
input_path = 'dataset/lakh'
if os.path.exists(output_path): shutil.rmtree(output_path)
os.mkdir(output_path)

list_ = os.listdir(input_path)
# list_ = [file_ for file_ in list_ if file_.startswith('Pet Shop Boys')]
t = tqdm(list_)
for f in t:
  path = os.path.join(input_path, f)
  t.set_description(path)
  if os.path.islink(path): continue
  # print(path)
  try:
    mid = mido.MidiFile(path)
  except Exception as e:
    t.write(f'Error processing file: {f}. Skipping...')
    continue
  tss = [msg for msg in mid if msg.type == 'time_signature']
  ts = tss[0].numerator if any(tss) else 3
  if ts.numerator not in [4]: continue
  mid.tracks = [mid.tracks[0]] + [track for track in mid.tracks if 'MELODY' in track.name.upper()]
  if len(mid.tracks) < 2: continue
  next(msg for msg in mid.tracks[1] if not msg.is_meta).time = 0
  mid.save(os.path.join(output_path, f))
