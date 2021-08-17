import pandas as pd
import argparse
import os 
import mido
import pathlib
import shutil

datasets = os.listdir('dataset')
files = [(dataset, filename)
  for dataset in datasets
  for filename in os.listdir(f'dataset/{dataset}')
  if any([filename.endswith(ext) for ext in ['.mid', '.midi']]) ]

for dataset, filename in files:
  try:
    mid = mido.MidiFile(f'dataset/{dataset}/{filename}')
    # print((dataset, filename))
    ts = next(msg for msg in mid if msg.type == 'time_signature')
    # print(ts.numerator)
    # if ts.numerator not in [2, 4]: continue
    if ts.numerator not in [4]: continue
    pathlib.Path(f'dataset/clean_{dataset}').mkdir(parents=True, exist_ok=True)
    shutil.copyfile(f'dataset/{dataset}/{filename}', f'dataset/clean_{dataset}/{filename}')

  except Exception as e:
    print(e)
# df = pd.DataFrame(files, columns=['filename', 'dataset', 'total_ticks'])

# print(df.head())

# df.to_pickle('output/df_dataset_status')