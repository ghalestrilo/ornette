# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %% [markdown]
# # Step 0: Basic Definitions + Dataset Analysis
# ---

# %%
import os
import subprocess
import glob
import json
from tqdm import tqdm
from time import monotonic
import pandas as pd
from itertools import islice, cycle
import pathlib
import shutil
import pickle
import random

## CONSTANTS
outputdir = os.path.abspath(os.path.join(os.curdir, 'output'))
barformat = "{bar}{r_bar}| ({percentage:.0f}%) | {desc}"

# Random Seeds
input_primers_random_state = 0
qa_samples_random_state = 0

# Directories
def output(*args):
    return os.path.join(outputdir, *args)

preprocessed_foldername = 'preprocessed'
preprocessed_dir = output(preprocessed_foldername)

# Define External Commands (Scripts)
def runscript(command=[], sibling_folder='tg-server', cwd=os.path.curdir, logfile=None):
    scriptdir=os.path.abspath(os.path.join(os.path.pardir, sibling_folder))
    subprocess.call(command, stdout=logfile, stderr=logfile, cwd=cwd)

# Delete everything inside a folder
def cleardir(dirname):
    print(f'Clearing {dirname}')
    if os.path.exists(dirname): shutil.rmtree(dirname)
    os.mkdir(dirname)

# Prepare Output Data Fields
metriccolumns = ['model', 'checkpoint', 'dataset', 'in_len', 'out_len', 'iteration']
out = []

iterations = 4         # How many times each experiment should be repeated for the same parameters?
min_input_bars = 1     # What is the minimum lookback size for each model?
min_output_bars = 1    # What is the minimum output size for each model?

max_input_bars = 6     # What is the maximum lookback size for each model?
max_output_bars = 6    # What is the maximum output size for each model?
sample_length = 16     # How long of a final composition should be generated? (Must equal primer_length)
primer_length = 16     # How long should each primer be? (in bars)
repeat_primers = False # Allow primer repetition? (useful for large primer lengths, when primer set becomes small)

extra_bars = 4        # Additional bars to generate at the end, to ensure we have enough (excess is trimmed)

max_primers = 15      # How many dataset samples should be used as primers for sequence

generation_path = '2021-09-19-3'


skip_dataset_prior_extraction = False




# %% [markdown]
# ### Script Testing Overrides
# 
# To test with fewer samples/iterations/lengths.
# Uncomment when running a final analysis

# %%
iterations = 8
max_primers = 6

# min_input_bars = 2    # What is the minimum lookback size for each model?
# min_output_bars = 2   # What is the minimum output size for each model?
# max_input_bars = 4    # What is the maximum lookback size for each model?
# max_output_bars = 4   # What is the maximum output size for each model?

skip_dataset_prior_extraction = True





# Declare Preprocessing Script
import mido
from scripts.analysis_scripts import extract_metrics, preprocess

# Prepare outputs
skip_preprocessing = [ None
    # , 'dataset'
    # , 'baseline'
    # , 'generation'
    ][1:]
if not any(skip_preprocessing): cleardir(preprocessed_dir)

write = lambda x: None

# Script Information
script_output_bpm = 60
desired_bars = sample_length # 16
desired_seconds = desired_bars * (60/script_output_bpm) # 32



  
  
def default_time_signature(filename):
    mid = mido.MidiFile(filename)
    tss = [msg for msg in mid if msg.type == 'time_signature']
    
    if any(mid.tracks) and not any(tss):
        mid.tracks[0].insert(0,mido.MetaMessage('time_signature',numerator=4,denominator=4,time=0))
        
    mid.save(filename)





logfile = open(output('preprocess.log'), 'w')

crop_sample = lambda filename: subprocess.call(cmd_crop(filename, filename, sample_length), stdout=logfile, stderr=logfile)

# Load data to preprocess
df_gen = pd.read_pickle(output('df_gen'))
gen_cols = ['model', 'checkpoint', 'in_len', 'out_len', 'dataset', 'iteration', 'out_file']



# Preprocess Dataset Samples
df_datasets = pd.read_pickle(output('df_dataset_features'))
datasetname = 'clean_lakh'
def get_dataset_samples(dataset_name, how_many):
    files = df_datasets[(df_datasets['dataset'] == dataset_name) & ((df_datasets['beats'] / df_datasets['bpm']) * 60 >= primer_length)]
    files = files.sample(how_many)['file'].values.tolist()
    # print(files)
    return enumerate(files)




prep_list = []

# Add Dataset Samples
if 'dataset' not in skip_preprocessing:
    cleardir(output(preprocessed_foldername, 'dataset'))
    prep_list += [(os.path.join('dataset', dataset_name, filename),
        output(preprocessed_foldername, 'dataset', dataset_name, str(index) + '-' + filename.split('/')[-1]),
        output(preprocessed_foldername, 'dataset', dataset_name),
        0)
        for dataset_name in df_gen['dataset'].unique()
        for (index, filename) in get_dataset_samples(dataset_name, max_primers)
        ]


# Add Baseline Samples
if 'baseline' not in skip_preprocessing:
    cleardir(output(preprocessed_foldername, 'baseline'))
    prep_list += [(
            output(generation_path, 'baseline', model, checkpoint, samplename),
            output(preprocessed_foldername, 'baseline', model, checkpoint, samplename),
            output(preprocessed_foldername, 'baseline', model, checkpoint),
            primer_length)
            # 0)
        for (model, checkpoint) in df_gen.groupby(['model', 'checkpoint']).groups
        for samplename in os.listdir(output(generation_path, 'baseline', model, checkpoint))]

# Add Generated samples
if 'generation' not in skip_preprocessing:
    cleardir(output(preprocessed_foldername, 'generation'))
    df_gen['out_file_prep'] = df_gen[gen_cols].apply(lambda row: ':'.join(row.values.astype(str)), axis=1)

    genlist = df_gen[gen_cols + ['out_file_prep', 'primer']].drop_duplicates().values.tolist()

    prep_list += [(output(out_file),
        output(preprocessed_foldername, 'generation', out_file_prep),
        '/'.join(output(preprocessed_foldername, 'generation', out_file_prep).split('/')[:-1]),
        0)
        for (model, checkpoint, in_len, out_len, dataset, iteration, out_file, out_file_prep, primer)
        in genlist]



# Run Preprocessing
# prep_list = prep_list[:730]
iterator = tqdm(prep_list)
for (in_filename, out_filename, out_path, start_bar) in iterator:
    write = tqdm.write
    # tqdm.write(', '.join([in_filename, out_filename, out_path, str(start_bar)]))
    pathlib.Path(out_path).mkdir(parents=True, exist_ok=True)
    if not os.path.exists(in_filename):
        tqdm.write(f'No Input: {in_filename}')
        continue
    iterator.set_description(in_filename)
    # try:
    #     preprocess(in_filename, out_filename, logfile, start_bar, sample_length*2)
    # except Exception as e:
    #     print(e)
    
    preprocess(in_filename, out_filename, logfile, start_bar, sample_length*2)

if 'generation' not in skip_preprocessing: df_gen.to_pickle(output('df_gen'))
logfile.close()