import mido
import os
import shutil
from tqdm import tqdm
import subprocess


output_path = "dataset/clean_lakh"
input_path = 'dataset/lakh'
if os.path.exists(output_path): shutil.rmtree(output_path)
os.mkdir(output_path)

## This script filters the Lakh dataset leaving behind only the melodies it can find
## Output: A set of Two-track MIDI files (conductor + melody)
max_samples = None
max_samples = 200
stretch_to_120_bpm = False 


# Script that streches everything to BPM
preprocess_scriptdir = os.path.abspath(os.path.join(os.path.pardir, 'miditools'))
preprocess_script = os.path.join(preprocess_scriptdir, 'midisox_py')
def cmd_preprocess(_in, _out):
  mid = mido.MidiFile(_in)
  tempo = next(msg for msg in mid if msg.type == 'set_tempo')
  factor = tempo.tempo / 500000 # Fix everybody to 120bpm
  return [ 'python', preprocess_script, os.path.abspath(_in), os.path.abspath(_out), 'tempo', str(factor)]








list_ = os.listdir(input_path)
if max_samples: list_ = list_[:max_samples]
# list_ = [file_ for file_ in list_ if file_.startswith('Pet Shop Boys')]
t = tqdm(list_)
for f in t:
  path = os.path.join(input_path, f)
  t.set_description(path)
  if os.path.islink(path): continue
  try:
    mid = mido.MidiFile(path)

    tss = [msg for msg in mid if msg.type == 'time_signature']
    ts = tss[0].numerator if any(tss) else 3
    if ts.numerator not in [4]: continue

    # Extract only melody
    melody_track = [track for track in mid.tracks[1:] if 'MELODY' in track.name.upper()]
    if any(melody_track): melody_track = melody_track[0]
    else: continue

    # Prepare conductor header (trim anything beyond start)
    conductor_track = mid.tracks[0]
    total_time = 0
    for msg in conductor_track:
      if hasattr(msg, 'time'): total_time += msg.time
      if total_time > 0: conductor_track.remove(msg)
    if conductor_track[-1].type != 'end_of_track': conductor_track.append(mido.MetaMessage('end_of_track', time=0))

    mid.tracks = [conductor_track, melody_track]
    if len(mid.tracks) != 2: continue
    next(msg for msg in mid.tracks[1] if not msg.is_meta).time = 0
    f = f.replace('\'','').replace('\\','').replace(' ','_') # Remove problematic chars from track name
    f = os.path.join(output_path, f)
    t.write(f'( {len(mid.tracks)} tracks) {f}')
    mid.save(f)
    
    if stretch_to_120_bpm:
      f = os.path.abspath(f)
      cmd = cmd_preprocess(f, f)
      subprocess.call(cmd)
  except Exception as e:
    t.write(f'Error processing file: {f}. Skipping...')
    print(e)
    # raise e
    continue
