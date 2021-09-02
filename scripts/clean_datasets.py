import pandas as pd
import argparse
import os 
import mido
import pathlib
import shutil

min_len = 0
# min_len = 4

prefix = 'clean_'
datasets = [path for path in os.listdir('dataset') if not path.startswith(prefix)]
# datasets = [path for path in os.listdir('dataset') if not path.startswith(prefix) and path.endswith('b-chorales')]
print(datasets)
# exit(1)
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
    shutil.copyfile(f'dataset/{dataset}/{filename}', f'dataset/{prefix}{dataset}/{filename}')


  except Exception as e:
    print(e)
# df = pd.DataFrame(files, columns=['filename', 'dataset', 'total_ticks'])

# print(df.head())

# df.to_pickle('output/df_dataset_status')