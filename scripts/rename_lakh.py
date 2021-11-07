import os
from tqdm import tqdm

datapath = 'dataset/clean_lakh'

t = tqdm(os.listdir(datapath))

for filename in t:
  new_filename = '_'.join(filename.split(' '))
  t.set_description(f'{filename} -> {new_filename}')
  os.rename(os.path.join(datapath,filename), os.path.join(datapath,new_filename))