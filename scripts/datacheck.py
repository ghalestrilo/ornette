import pandas as pd
import argparse
import os 
import mido



def get_total_ticks(filename):
  try:
    mid = mido.MidiFile(filename)
    tempo = [msg.tempo for msg in mid if msg.type == 'set_tempo']
    tempo = tempo[0] if any(tempo) else 500000
    return sum(mido.second2tick(msg.time, tempo=tempo, ticks_per_beat=mid.ticks_per_beat) for msg in mid if not msg.is_meta)
  except Exception as e:
    print(f'error with: {filename}')
    print(e)
    return 0




datasets = os.listdir('dataset')
files = [[filename, dataset, get_total_ticks(f'dataset/{dataset}/{filename}')]
  for dataset in datasets
  for filename in os.listdir(f'dataset/{dataset}')
  if any([filename.endswith(ext) for ext in ['.mid', '.midi']]) ]

df = pd.DataFrame(files, columns=['filename', 'dataset', 'total_ticks'])

print(df.head())

df.to_pickle('output/df_dataset_status')