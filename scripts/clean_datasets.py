import pandas as pd
import argparse
import os 
import mido
import pathlib
import shutil
import subprocess

min_len = 0
# min_len = 4

prefix = 'clean_'
datasets = [path for path in os.listdir('dataset') if not path.startswith(prefix)]
# datasets = [path for path in os.listdir('dataset') if not path.startswith(prefix) and path.endswith('b-chorales')]
print(datasets)



cmd_preprocess = lambda _in, _out: 

def cmd_preprocess(_in, _out):
  mid = mido.MidiFile(_in)
  tempo = next(msg for msg in mid if msg.type == 'set_tempo')
  factor = tempo / 500000 # Fix everybody to 120bpm
  return [ 'python', preprocess_script, os.path.abspath(_in), os.path.abspath(_out), 'tempo', factor]


files = [(dataset, filename)
  for dataset in datasets
  for filename in os.listdir(f'dataset/{dataset}')
  if any([filename.endswith(ext) for ext in ['.mid', '.midi']]) ]

for dataset, filename in files:
  try:
    mid = mido.MidiFile(f'dataset/{dataset}/{filename}')
    ts = next(msg for msg in mid if msg.type == 'time_signature')
    if ts.numerator not in [4]: continue
    if mid.length()< min_len: continue
    pathlib.Path(f'dataset/{prefix}{dataset}').mkdir(parents=True, exist_ok=True)
    cmd = cmd_preprocess(f'dataset/{dataset}/{filename}', f'dataset/{prefix}{dataset}/{filename}')
    subprocess.call(cmd)
    # shutil.copyfile(f'dataset/{dataset}/{filename}', f'dataset/{prefix}{dataset}/{filename}')


  except Exception as e:
    print(e)
# df = pd.DataFrame(files, columns=['filename', 'dataset', 'total_ticks'])

# print(df.head())

# df.to_pickle('output/df_dataset_status')