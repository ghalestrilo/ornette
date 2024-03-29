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

# %% [markdown]
# ### Extract basic dataset metrics

# %%
import pandas as pd
import argparse
import os 
import mido

dataset_columns = ['dataset', 'file', 'bpm', 'ticks', 'tpb', 'tracks', 'error']

def get_dataset_metrics(filename, t=None):
  try:
    # tqdm.write(filename)
    mid = mido.MidiFile(filename)
    tempo = [msg.tempo for msg in mid if msg.type == 'set_tempo']
    tempo = tempo[0] if any(tempo) else 500000
    bpm = mido.tempo2bpm(tempo)
    tpb = mid.ticks_per_beat
    tracks = len(mid.tracks)
    total_time = sum(mido.second2tick(msg.time, tempo=tempo, ticks_per_beat=tpb) for msg in mid if not msg.is_meta)
    ret =  [bpm, total_time, tpb, tracks, False]
    if t: t.set_description(", ".join([filename] + list(map(str, ret))))
    # if t: tqdm.write(", ".join([filename] + list(map(str, ret))))
    return ret
  except Exception as e:
    # print(f'error with: {filename}')
    print(e)
    return [0, 0, True]

if skip_dataset_prior_extraction == False:
  datasets = os.listdir('dataset')
  datasets = [d for d in datasets if d.startswith('clean_')]
  # datasets = [d for d in datasets if d.startswith('mtd')]
  files = tqdm([(dataset, filename)
    for dataset in datasets
    for filename in os.listdir(f'dataset/{dataset}') # [:2]
    if any([filename.endswith(ext) for ext in ['.mid', '.midi']]) ])
    
  # Create DataFrame
  files = [[dataset, filename] + get_dataset_metrics(f'dataset/{dataset}/{filename}', files)
    for dataset, filename in files]
  df_datasets = pd.DataFrame(files, columns=dataset_columns)

  # Calculate sample bar length
  df_datasets['beats'] = df_datasets['ticks'].astype(int) / df_datasets['tpb'].astype(int)
  df_datasets['bars'] = df_datasets['beats'].astype(float).round() / 4

  print(df_datasets.head())
  if True in df_datasets['error'].unique():
      errloc = df_datasets.loc[df_datasets['error'] == True]
      print(f"{len(errloc.values.tolist())} errors found during dataset analysis")
      print(errloc)

  # Rename spaces to underscores
  df_datasets.loc[df_datasets['dataset'] == 'clean_lakh', 'file'] = df_datasets.loc[df_datasets['dataset'] == 'clean_lakh']['file'].apply(lambda name: '_'.join(name.split(' ')))
  df_datasets.loc[df_datasets['dataset'] != 'clean_lakh', 'file']
  df_datasets['bar_duration_ms'] = 4 * (60000 / df_datasets['bpm'])
  df_datasets.to_pickle('output/df_dataset_features')

# %% [markdown]
# # Step 1: Generation Phase
# ---
# %% [markdown]
# ## Definitions

# %%

import os
import sys
import subprocess
import pandas as pd
from datetime import date

outputdir = os.path.join(os.path.curdir, 'output')
env = os.environ.copy()

home_dir = os.path.expanduser('~')

# Directories to mount on docker call
ORNETTE_PATH    = env['ORNETTE_PATH']    if 'ORNETTE_PATH'    in env.keys() else os.path.join(home_dir, 'git', 'tg-server')
CHECKPOINT_PATH = env['CHECKPOINT_PATH'] if 'CHECKPOINT_PATH' in env.keys() else os.path.join(home_dir, '.ornette', 'checkpoints')
OUTPUT_PATH     = env['OUTPUT_PATH']     if 'OUTPUT_PATH'     in env.keys() else os.path.join(ORNETTE_PATH, 'output')
DATASET_PATH    = env['DATASET_PATH']    if 'DATASET_PATH'    in env.keys() else os.path.join(ORNETTE_PATH, 'dataset')

barcount = 16

def checkpath(modelname, checkpointname):
    dirname = output('baseline', modelname, checkpointname)
    if not os.path.exists(dirname): os.mkdir(dirname)

ornette_docker_call = (
    [ 'docker' , 'run'
    , '-v'     , f'{CHECKPOINT_PATH}:/checkpoints'
    , '-v'     , f'{OUTPUT_PATH}:/output'
    , '-v'     , f'{DATASET_PATH}:/dataset'
    ]
)

# Generation Output Directory
generation_path = str(date.today())
generation_index = list(folder.split('-')[-1] for folder in os.listdir(output('')) if folder.startswith(generation_path))
generation_index = [int(index) for index in generation_index if index]
generation_index = max(generation_index) + 1 if any(map(str, generation_index)) else 0
generation_path += f'-{generation_index}'
os.mkdir(output(generation_path))

# %% [markdown]
# ## Ornette Sample Generation Code

# %%
# Get Args, define evaluation groups

# ignore = (            # What models to ignore during generation/analysis
#   [ ''
#   # FIXME: These are temporary - shit went wrong
#   # , 'rl_duet'            
#   # , 'pianoroll_rnn_nade'
#   # , 'polyphony_rnn'
#   # , 'melody_rnn'
#   # , 'performance_rnn'
#   ] 
# )

# Evaluated Model Table
eval_columns = (
    ['model'               , 'dataset'       , 'output_tracks' , 'checkpoint']
)
eval_list = (
  [ None
  , ['performance_rnn'     , 'clean_piano-e-comp'  , None            , 'performance_with_dynamics']
  # , ['performance_rnn'     , 'clean_piano-e-comp'  , None            , 'density_conditioned_performance_with_dynamics']
  # , ['performance_rnn'     , 'clean_piano-e-comp'  , None            , 'pitch_conditioned_performance_with_dynamics']
  # , ['performance_rnn'     , 'clean_piano-e-comp'  , None            , 'multiconditioned_performance_with_dynamics']
  # , ['performance_rnn'     , 'clean_piano-e-comp'  , None            , 'performance_with_dynamics_and_modulo_encoding']

  , ['melody_rnn'          , 'clean_lakh'      , '1'            , 'attention_rnn']
  # , ['melody_rnn'          , 'clean_lakh'      , 1            , 'basic_rnn']
  # , ['melody_rnn'          , 'clean_lakh'      , 1            , 'mono_rnn']
  # , ['melody_rnn'          , 'clean_lakh'      , 1            , 'lookback_rnn']
  
  , ['polyphony_rnn'       , 'clean_jsb-chorales'        , None            , 'polyphony_rnn']
  , ['pianoroll_rnn_nade'  , 'clean_jsb-chorales'        , None            , 'rnn-nade_attn']
  # , ['rl_duet'             , 'clean_jsb-chorales'        , None            , 'rl_duet']

  # # Don't use any of these configs
  # , ['rl_duet'             , 'clean_bach10'        , None            , 'rl_duet']
  # , ['polyphony_rnn'       , 'clean_bach10'        , None            , 'polyphony_rnn']
  # , ['pianoroll_rnn_nade'  , 'clean_bach10'        , None            , 'rnn-nade_attn']
  # , ['melody_rnn'          , 'clean_mtd-orig'      , None            , 'basic_rnn']
  # , ['melody_rnn'          , 'clean_mtd-orig'      , None            , 'mono_rnn']
  # , ['melody_rnn'          , 'clean_mtd-orig'      , None            , 'attention_rnn']
  # , ['melody_rnn'          , 'clean_mtd-orig'      , None            , 'lookback_rnn']
  # , ['music_transformer'   , 'clean_piano-e-comp'  , None            , 'performance_with_dynamics']
  ][1:]
)
eval_list = pd.DataFrame(eval_list, columns=eval_columns)

# Filter ignored models
# for ignored_model in ignore:
  # eval_list = eval_list[eval_list['model'] != ignored_model]

# Index table with dataset names
evaluation_sets = [
  (dataset, [ (modelname, checkpoint, output_tracks)
    for [modelname, checkpoint, output_tracks]
    in inner_df[['model', 'checkpoint', 'output_tracks']].values 
  ])
  for dataset, inner_df in eval_list.groupby(['dataset'])
]

cols_gen = [ "model", "checkpoint", "dataset", "primer", "iteration", "out_file", "time", "in_len", "out_len" ]


# %%
# Generation Methods

from functools import reduce
import re
import math

# Prepare a command string to send to ornette via CLI
def escape_command(commands):
  commands = re.split('\n|;', commands)
  commands = [line.split(' ') for line in commands]
  commands = [cmd for cmd in commands if any(cmd)]
  # commands = ['\ '.join(line) for line in commands]
  commands = [' '.join(line) for line in commands]
  # commands = '\;'.join(commands)
  commands = ';'.join(commands)
  commands = re.escape(commands)
  commands = commands.replace(';','\;')
  return commands

def get_filename(modelname, checkpointname, primer, index, bars_input, bars_output):
  return f'{generation_path}/{modelname}-{checkpointname}-{index}-{bars_input}-{bars_output}-{primer}'

# WIP: another approach, via CLI args
def get_generation_command(the_modelname, the_checkpointname, output_tracks, datapath, primer, bars_input, bars_output, count):
  # Reset, load the primer again, generate, save
  exec_cmd = [';\n'.join(
      [ 'reset'
      , f'load /{datapath}/{primer} {bars_input}'
      # , exec_cmd
      , f'generate_to {sample_length}'
      , f'drop_primer'
      , f'save {get_filename(the_modelname, the_checkpointname, primer, index, bars_input, bars_output)}'
      ]
    )
    for index
    in range(count)]
  
  # Before running generation: set variables
  exec_vars = [ 'set debug_output True;'
    , 'set batch_mode True;'
    , 'set playback False;'
    , 'set debug_output False;'
    , f'set input_length {bars_input};'
    , f'set input_unit bars;'
    # , f'set output_length {bars_output};'
    # , f'set output_unit bars;'
  ]

  if output_tracks: exec_vars.append('set output_tracks ' + output_tracks + ';')

  # Combine Lines
  exec_cmd = '\n'.join(exec_vars + exec_cmd + ['end'])

  # Escape string to pass it via CLI
  exec_cmd = escape_command(exec_cmd)
  print(exec_cmd)
  return exec_cmd

logfile = None
def generate_samples(the_modelname, the_checkpointname, output_tracks, datapath, primer, bars_input, bars_output, count, t):
    customprint = t.set_description if t else log
    # Set logging prefix
    modelname = the_modelname
    checkpointname = the_checkpointname
    t.set_description(f'Generating ({modelname}:{checkpointname}) samples with {primer}')

    # Get Ornette CLI command
    if datapath.startswith('.'): datapath = datapath[1:]
    cmd = get_generation_command(the_modelname, the_checkpointname, output_tracks, datapath, primer, bars_input, bars_output, count)
    # t.write(cmd)

    # Process filenames
    filenames = [get_filename(the_modelname, the_checkpointname, primer, index, bars_input, bars_output) for index in range(count)]


    # Run (and time) the generation batch
    logfilename = output(f'{the_modelname}-{the_checkpointname}.log')
    logfile = open(logfilename, 'a')

    start_time = monotonic()
    server = subprocess.run(
      ['python' , '.' , '--modelname' , modelname , '--checkpoint' , checkpoint , '--exec' , cmd , '--no-server=True']
      , env=env
      , stdout=logfile
      , stderr=logfile
      )
    end_time = monotonic()
    
    # Calculate total generation time
    gentime = (end_time - start_time) / count
    return [(filenames, gentime)]

def run_generation(model, checkpoint, datapath, primers, output_tracks):
  logfilename = output(f'{model}-{checkpoint}.log')
  with open(logfilename,'w') as logfile:
    print('\n', file=logfile)
  
    t = tqdm(([ model, checkpoint, dataset, primer
        , iterations # TODO: pass iterations to generate samples / use iterations here
        , filename, gentime, bars_input, bars_output]
    for bars_input in range(min_input_bars,max_input_bars + 1)
    for bars_output in range(min_output_bars,max_output_bars + 1)
    for primer in primers
    for (filenames, gentime) in generate_samples(model, checkpoint, output_tracks, datapath, primer, bars_input, bars_output, iterations, t)
    for filename in filenames),
    bar_format=barformat)
  
  return list(t)

# %% [markdown]
# ### Generate Samples

# %%
df_datasets = pd.read_pickle('output/df_dataset_features')

def get_primers(dataset, count):
    print(f'{dataset}:{count}')
    minimum_length = primer_length # NOTE: Setting this too high may remove all samples from the input data. 4 is an ideal value
    df_tmp = df_datasets.loc[(df_datasets['bars'] >= minimum_length) & (df_datasets['dataset'] == dataset)].sample(count, random_state=input_primers_random_state, replace=repeat_primers)
    return df_tmp['file'].values


try:
    tqdm.write(f'Starting experiment suite: {outputdir}/{generation_path}')

    # Set logging prefix
    output_rows = []
    for dataset, models in evaluation_sets:
        if dataset is None: continue
        datapath = os.path.join('dataset', dataset)
        # primerdir = datapath
        if not os.path.exists(datapath):
            print(f'Directory not found: {datapath}, skipping')
            continue

        # Select primers from dataset
        primers = get_primers(dataset, max_primers)
        # print(primers)
        total_samples = iterations * len(primers) * (max_input_bars - min_input_bars + 1) * (max_output_bars - min_output_bars + 1)
        tqdm.write(f'Generating data for {len(primers)} primers ({total_samples} samples total)')

        # Run a generation batch with the chosen samples
        for (model, checkpoint, output_tracks) in models:
            expname = model
            e = run_generation(model, checkpoint, datapath, primers, output_tracks)
            output_rows += e

    # Create DataFrame
    df = pd.DataFrame(output_rows, columns=cols_gen)
    df.to_pickle(output('df_gen'))
    

except KeyboardInterrupt:
  tqdm.write("Terminating...")

tqdm.write("Done!")

# %% [markdown]
# ### Filter Generated Output
# 
# The cell below removes from the dataframe the data about models that had issues with generation. It notifies what model:checkpoints are being removed.
# 
# If this happens, check the .log file for more information, there will probably be a python exception somewhere.
# %% [markdown]
# ## Baseline Sample Generation Code

# %%
# Generation Scripts

## Magenta Models

### MelodyRNN: Generate samples
melody_rnn_cmd = lambda checkpoint, primer, barcount, number_of_samples: (
    ornette_docker_call + 
    [ '-t'    , 'ornette/melody_rnn'
    , 'melody_rnn_generate'
    , f'--config={checkpoint}'
    , f'--bundle_file=/checkpoints/melody_rnn/{checkpoint}'
    , f'--output_dir=/output/{generation_path}/baseline/melody_rnn/{checkpoint}'
    , f'--num_outputs={iterations}'
    , f'--num_steps={(sample_length + primer_length + extra_bars) * 4 * 4}'
    , f'--primer_midi={primer}'
    ]
)

### PerformanceRNN: Generate samples
performance_rnn_cmd = lambda checkpoint, primer, barcount, number_of_samples: (
    ornette_docker_call + 
    [ '-t'    , 'ornette/performance_rnn'
    , 'performance_rnn_generate'
    , f'--config={checkpoint}'
    , f'--bundle_file=/checkpoints/performance_rnn/{checkpoint}'
    , f'--output_dir=/output/{generation_path}/baseline/performance_rnn/{checkpoint}'
    , f'--num_outputs={iterations}'
    , f'--num_steps={(sample_length + primer_length + extra_bars) * 2 * 100}'
    , f'--primer_midi={primer}'
    ]
)

### PianorollRNN-NADE: Generate Samples
pianoroll_rnn_nade_cmd = lambda checkpoint, primer, barcount, number_of_samples: (
    ornette_docker_call + 
    [ '-t'    , 'ornette/pianoroll_rnn_nade'
    , 'pianoroll_rnn_nade_generate'
    , f'--config=rnn-nade_attn'
    , f'--bundle_file=/checkpoints/pianoroll_rnn_nade/{checkpoint}'
    , f'--output_dir=/output/{generation_path}/baseline/pianoroll_rnn_nade/{checkpoint}'
    , f'--num_outputs={iterations}'
    , f'--num_steps={(sample_length + primer_length + extra_bars) * 4 * 4}'
    , '--condition_on_primer=true'
    , '--inject_primer_during_generation=false'
    , f'--primer_midi={primer}'
    ]
)   

### PolyphonyRNN: Generate Samples
polyphony_rnn_cmd = lambda checkpoint, primer, barcount, number_of_samples: (
    ornette_docker_call + 
    [ '-t'    , 'ornette/polyphony_rnn'
    , 'polyphony_rnn_generate'
    , f'--config=rnn-nade_attn'
    , f'--bundle_file=/checkpoints/polyphony_rnn/{checkpoint}'
    , f'--output_dir=/output/{generation_path}/baseline/polyphony_rnn/{checkpoint}'
    , f'--num_outputs={iterations}'
    , f'--num_steps={(sample_length + primer_length + extra_bars) * 4 * 4}'
    , '--condition_on_primer=true'
    , '--inject_primer_during_generation=false'
    , f'--primer_midi={primer}'
    ]
)

# List of generation scripts
baseline_generation_commands = {
    'melody_rnn': melody_rnn_cmd,
    'performance_rnn': performance_rnn_cmd,
    'pianoroll_rnn_nade': pianoroll_rnn_nade_cmd,
    'polyphony_rnn': polyphony_rnn_cmd,
}

# Crop a midi file (via ornette)
cmd_crop = lambda input_file, output_file, _length: (
    ['python'
    , '.'
    , '--no-server'
    , 'true'
    , '--no-module'
    , 'true'
    , '--modelname'
    , 'melody_rnn'
    , '--checkpoint'
    , 'basic_rnn'
    , '--exec'
    , '\;'.join(
        [ 'reset'
        , f'load\ {input_file}\ 8000'
        , f'crop\ bars\ 0\ {_length}'
        , f'save\ {output_file}'
        , 'end'
        ])
    ]
)


# %%
# Read generation data
df_gen = pd.read_pickle(output('df_gen'))

import sys
from scripts.analysis_scripts import extract_metrics, preprocess

# Determine how many samples to generate
number_of_samples = max_primers
for col in ['out_file','time','in_len','out_len']:
    if col in df_gen.columns:
        df_gen = df_gen.drop(columns=[col])


# Clear 'tmp' folder
tmp_foldername = 'tmp_baseline'
models = df_gen['model'].unique()
print(f'Generating baseline samples for: {models}')
cleardir(output(tmp_foldername))
cleardir(output('baseline'))

# Create iterator
df_gen = df_gen.groupby(['model', 'checkpoint', 'dataset', 'primer']).count().reset_index()
df_iterator = tqdm(df_gen.values.tolist(), bar_format=barformat)

logfile = open(output('baseline.log'), 'w')

# Baseline Sample Generation Loop
for row in df_iterator:

    model = row[0]
    checkpoint = row[1]
    dataset = row[2]
    primer = row[3]
    
    try:
        baseline_generation_command = baseline_generation_commands[model]
    except KeyError:
        df_iterator.set_description(f'{model}:{checkpoint} has no baseline model. Skipping...')
        continue
    
    df_iterator.set_description(f'{model}:{checkpoint} ({primer})')

    print(f'Starting generation of baseline samples for {model}:{checkpoint}\n', file=logfile)

    # Crop Dataset Samples (/dataset -> /output/tmp_baseline)
    outputpath = output(tmp_foldername, primer)
    if not os.path.exists(outputpath):
        extless = primer.split('.')
        # extless = primer.split('.')[:-1]
        extless = '.'.join(extless)
        dataset_samplepath = f'dataset/{dataset}/{primer}' # Directory is inside container
        dataset_outputpath = f'output/{tmp_foldername}/{extless}'  # Directory is inside container
        preprocess(dataset_samplepath, dataset_outputpath, desired_seconds=primer_length*2)
        
        # runscript(prepscript(os.path.abspath(dataset_samplepath), os.path.abspath(dataset_outputpath), 'trim', '0', str(primer_length)))

        # command = cmd_crop(dataset_samplepath, dataset_outputpath, primer_length)
        # runscript(cmd_crop(dataset_samplepath, dataset_outputpath, primer_length))
        # subprocess.call(command, stdout=logfile, stderr=logfile, cwd=ORNETTE_PATH)
        # shutil.copyfile(dataset_samplepath, dataset_outputpath)

    # Generate Baseline Samples (/tmp_baseline -> /output/baseline/<model>/<checkpoint>)
    command = baseline_generation_command
    primer_path = f'/output/{tmp_foldername}/{primer}'      # Directory is inside container
    if not os.path.exists(primer_path[1:]): raise FileNotFoundError(primer_path)
    command = command(checkpoint, primer_path, barcount, number_of_samples)
    subprocess.call(command, stdout=logfile, stderr=logfile)

logfile.close()

# %% [markdown]
# # Step 2: Feature Extraction
# %% [markdown]
# ## Preprocess Samples

# %%
# Declare Preprocessing Script
import mido
from scripts.analysis_scripts import extract_metrics, preprocess

# Prepare outputs
skip_preprocessing = [ None
    , 'dataset'
    , 'baseline'
    , 'generation'
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


# %%

# Declare analysis script
metricsfile = output('metrics_gen')
extraction_scriptdir = os.path.abspath(os.path.join(os.path.pardir, 'mgeval'))
extraction_script = os.path.join(extraction_scriptdir, 'start.sh')
cmd_extraction = lambda dataset_1, dataset_2, output_pickle_filename: [
    'bash',
    extraction_script,
    os.path.abspath(dataset_1),
    os.path.abspath(dataset_2),
    output_pickle_filename,
    str(sample_length)
]

# %% [markdown]
# ## Extract Features from Samples

# %%
generation_columns = ['model', 'checkpoint', 'dataset', 'in_len', 'out_len', 'iteration']

# Prepare output
if os.path.exists(metricsfile): os.remove(metricsfile)
logfile = open(output('extraction.log'), 'w')

metrics_columns = []

# Extract metrics between two different datasets
print('Extracting metrics from generated output', file=logfile)
def extract_metrics(samples_path, dataset_path, logfile, iterator):
    iterator.set_description(f'Analyzing samples inside: {samples_path}')

    # Clear previous metrics
    if os.path.exists(metricsfile): os.remove(metricsfile)
 
    # Extract features
    subprocess.call(cmd_extraction(samples_path, dataset_path, os.path.abspath(metricsfile)), stdout=logfile, stderr=logfile, cwd=extraction_scriptdir)

    # Read extracted features
    try:
        with open(metricsfile, 'r') as metricsfile_:
            row_metrics = json.load(metricsfile_)
            if not any(metrics_columns):
                for metric in row_metrics.keys():
                    metrics_columns.extend([metric + '_kl_div', metric + '_overlap'])

        row = []
        for metric in row_metrics.keys():
            [_mean, _std, _kl_div, _overlap, _training_set_kl_div, _training_set_overlap] = row_metrics[metric]
            row.extend([ _kl_div, _overlap ])

        return row.copy()
    except FileNotFoundError:
        return [None for _ in range(6)]

# Load data for feature extraction
df_gen = pd.read_pickle(output('df_gen'))
df_gen['prepped_sample_dir'] = df_gen['out_file_prep'].apply(lambda name: '/'.join(name.split('/')[:-1]))
grouping = df_gen.groupby(['model', 'checkpoint', 'in_len', 'out_len', 'dataset', 'iteration', 'prepped_sample_dir'])

generated_saples_iterator = tqdm(grouping.groups, bar_format=barformat)

# Extract metrics from Generation Output
out = [[model, checkpoint, dataset, inn, outn, iteration]
    + extract_metrics(
        output(preprocessed_foldername, 'generation', prepped_sample_dir),
        output(preprocessed_foldername, 'dataset', dataset),
        logfile,
        generated_saples_iterator)
    for (model, checkpoint, inn, outn, dataset, iteration, prepped_sample_dir)
    in generated_saples_iterator
]
errs = [x for x in out if x[-1] is None]
out = [x for x in out if x[-1] is not None]
final_columns = generation_columns + metrics_columns

# Save values to output DF
df_extracted_metrics = pd.DataFrame(out, columns=final_columns)

df = df_gen.merge(pd.DataFrame(out, columns=final_columns), how='inner', on=generation_columns)
df.to_pickle(output('df_metrics_generation'))


# Create Iterator
baseline_columns = ['model', 'checkpoint', 'dataset']
grouping = df_gen.groupby(baseline_columns)
baseline_list = tqdm(grouping.groups, bar_format=barformat)
groupinggrid = [[model, checkpoint, dataset] for (model,checkpoint,dataset) in grouping.groups]
out = [[model, checkpoint, dataset]
    + extract_metrics(
        output(preprocessed_foldername, 'baseline', model, checkpoint),
        output(preprocessed_foldername, 'dataset', dataset),
        logfile,
        baseline_list)
    for model, checkpoint, dataset in baseline_list
]
final_columns = baseline_columns + metrics_columns
df = pd.DataFrame(out, columns=final_columns)
df.to_pickle(output('df_metrics_baseline'))

df_baseline = pd.read_pickle(output('df_metrics_baseline'))

logfile.close()


# %%
df.groupby('model').mean()














# %% [markdown]
# # Step 3: Feature Analysis + Plotting
# ---
# %% [markdown]
# ## Definitions

# %%
# Definitions for next plots

# Constants
figdir = os.path.join('output', 'images')
figure_output = lambda name: os.path.join(figdir, name)

ignore_words = ['std', 'avg', 'kl', 'div', 'overlap']
def filter_metric_names(list_):
    return ['_'.join([x for x in name.split('_') if x not in ignore_words]) for name in list_]

# Define which plots to make
plots_to_make = (
    [ None
    # , 'time_heatmap_per_model'
    # , 'kldiv_per_model'
    # , 'overlap_per_model'
    # , 'time_per_length'
    # , 'time_ratio_per_length'
    # , 'time_per_length_shared' # TODO: Before doing this, check if there's a correlation

    # , 'time_per_length_shared'
    , 'parallel_coordinates_all_configs'
    , 'parallel_coordinates_average'
    , 'parallel_coordinates_best_of_each'
    , 'heatmap_metric_per_config'
    # , 'heatmap_metrics_per'
    , 'point_plot_best_vs_baseline'
    ]
)

import math

# %% [markdown]
# ## Calculate Mean Metric Ovelap and KL-Divergence against Dataset (per model, per configuration)

# %%
# Create 'config' column, group by model:checkpoint:config
df_by_config = pd.read_pickle(os.path.join(outputdir, 'df_metrics_generation'))
df_by_config['config'] = df_by_config["in_len"].astype(str) + '_' + df_by_config["out_len"].astype(str)
df_by_config.drop(columns=['in_len','out_len','iteration'])
# print(df_by_config.head())
df_by_config = df_by_config.groupby(['model','checkpoint','config']).mean().reset_index()

# Get Subset DFs
col_metrics = df_by_config.columns
col_kl_divs  = [x for x in col_metrics if x.endswith('kl_div')]
col_overlaps = [x for x in col_metrics if x.endswith('overlap')]

# Calculate KL Divs mean and std per model config
loc_kldivs = df_by_config[['model'] + col_kl_divs].loc[: , "bar_pitch_class_histogram_kl_div":"note_length_hist_kl_div"]
df_by_config['kl_mean'] = loc_kldivs.mean(axis=1)
df_by_config['kl_std'] = loc_kldivs.std(axis=1)
loc_overlaps = df_by_config[['model'] + col_overlaps].loc[: , "bar_pitch_class_histogram_overlap":"note_length_hist_overlap"]
df_by_config['overlap_mean'] = loc_overlaps.mean(axis=1)
df_by_config['overlap_std'] = loc_overlaps.std(axis=1)
df_mean_metrics = df_by_config.copy()

df_mean_metrics.head()
# TODO: Make this a function, so we can call it with df_metrics_baseline

# %% [markdown]
# ## Plotting Code

# %%
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns 

# %% [markdown]
# ### Filter configurations by consumption/generation ratio for own dataset's mean BPM

# %%

titles = ['Todas as Configurações', 'Apenas Configurações Dinamicamente Viáveis']
labels = ['Tempo de Geração (ms/Compasso)', 'Configuração (Entrada sobre Saída)']
# labels = ['Generation Time (ms/Bar)', 'Configuração (Entrada:Saída)']

recalc = True
filter_bpm = False

if recalc and 'real_time_capable' in df_mean_metrics.columns:
    df_mean_metrics = df_mean_metrics.drop(columns=['real_time_capable'])

# Clear df_mean_metrics if re-running
df_mean_metrics = df_mean_metrics.drop(columns=[col for col in df_mean_metrics if col.startswith('subject')])

# Read features extracted from dataset
df_time = pd.read_pickle(output('df_dataset_features'))
df_time = df_time.groupby('dataset').mean().reset_index()
#df_time = df_time.rename(columns={'bpm': 'mean_bpm', 'ticks': 'mean_ticks'})
df_time = df_time.rename(columns={'bpm': 'mean_bpm', 'ticks': 'mean_ticks'})
print(df_time.columns)

# Read generation metrics
df_gen = pd.read_pickle(output('df_metrics_generation'))
df_time = df_gen.merge(df_time, how='inner', on=['dataset'])

# How to calculate this? (iterations * max_primers)
samples_per_request = 1
samples_per_request = iterations * max_primers
print(samples_per_request)

# Calculate time values
# df_time['time'] /= samples_per_request
df_time['bar_duration_ms'] = 4 * (60000 / df_time['mean_bpm'])
df_time['bar_generation_ms'] = 1000 * df_time['time'] / (sample_length + extra_bars)
# 60000 / BPM = one beat in milliseconds

df_time = df_time.groupby(['model', 'checkpoint', 'in_len', 'out_len']).mean()
df_time = df_time.reset_index()

# Determine if a model is real-time capable
df_time['real_time_capable'] = df_time['bar_generation_ms'] < df_time['bar_duration_ms']
df_time['real_time_capable'] = df_time['real_time_capable'].astype(str)

# Plot generation time
df_time['config'] = df_time["in_len"].astype(str) + '_' + df_time["out_len"].astype(str)
df_time['subject'] = df_time["model"].astype(str) + '_' + df_time["checkpoint"].astype(str)
# df_time[['dataset', 'bar_duration_ms', 'mean_bpm']].drop_duplicates().to_pickle(output('df_dataset_times'))
# df_time.to_pickle(output('df_dataset_times'))

# Lineplot: All configurations
tmp_df = df_mean_metrics.merge(df_time[['model','checkpoint','config','real_time_capable', 'subject', 'bar_generation_ms']], on=['model', 'checkpoint', 'config'])
fig = plt.figure(figsize=(10,5), dpi=120)
# sns.set_theme(style='darkgrid')
sns.set_style("whitegrid")
tmp_df['config'] = tmp_df['config'].apply(lambda x: x.replace('_','\n'))
tmp_df['Dinamicamente Viável'] = tmp_df['real_time_capable'].apply( lambda x: 'Sim' if x else 'Não')
tmp_df['Modelo'] = tmp_df['subject']
g = sns.lineplot(data=tmp_df, y='bar_generation_ms', x='config', hue='Modelo', err_style="bars", ci=68, markers=True, dashes=False)
fig.get_axes()[0].legend(loc='center left',fontsize='small', frameon=False, title="Modelo")
# plt.title(titles[0])
g.set_ylabel(labels[0])
g.set_xlabel(labels[1])
plt.savefig(figure_output('lineplot_all_configurations'))

# Filter configuration - select those those that can be used in real time
if 'real_time_capable' not in df_mean_metrics.columns and filter_bpm:
    # print(tmp_df.groupby('real_time_capable').head())
    df_mean_metrics = tmp_df.loc[tmp_df['real_time_capable'] == 'True']

modelnames = {
  'melody_rnn:attention_rnn:attention_rnn': 'MelodyRNN',
  'performance_rnn:performance_with_dynamics:performance_with_dynamics': 'PerformanceRNN',
  'pianoroll_rnn_nade:rnn-nade_attn:rnn-nade_attn': 'PianorollRNN-NADE',
  'polyphony_rnn:polyphony_rnn:polyphony_rnn': 'PolyphonyRNN'
}

# Lineplot: Selected Configurations
fig = plt.figure(figsize=(10,6), dpi=200)
df_mean_metrics['subject'] = df_mean_metrics['model'].astype(str) + ':' + df_mean_metrics['checkpoint'].astype(str) + ':' + df_mean_metrics['checkpoint'].astype(str)
tmp_df = df_mean_metrics.copy()
tmp_df = tmp_df.merge(df_time[['model','checkpoint','config','real_time_capable', 'bar_generation_ms']], on=['model', 'checkpoint', 'config'])
tmp_df['config'] = tmp_df['config'].apply(lambda x: x.replace('_','\n'))
tmp_df['Modelo'] = tmp_df['subject'].apply(lambda x: modelnames[x])
g = sns.lineplot(data=tmp_df, y='bar_generation_ms', x='config', hue="Modelo", err_style="bars", ci=68, markers=True, dashes=False)
fig.get_axes()[0].legend(loc='center left',frameon=False,title="Modelo")
# plt.title(titles[1])
g.set_ylabel(labels[0])
g.set_xlabel(labels[1])
plt.savefig(figure_output('lineplot_selected_configurations'))

tmp_df = df_time[['subject', 'time', 'in_len', 'out_len', 'bar_duration_ms', 'bar_generation_ms', 'mean_bpm']]
tmp_df.to_pickle(output('df_time_filtered'))
tmp_df.to_csv(output('df_time_filtered.csv'))
tmp_df.head()


# %%
# title = 'Impact of Input/Output Length Pair over Key Metrics'
title = 'Impacto da Configuração sobre a Média entre Métricas'
labels = ['Modelo', 'Configuração']
subtitles = ['Overlap Médio entre Métricas', 'KL-Divergência Médio entre Métricas']
# subtitles = ['Overlap Mean', 'KL-Divergence Mean']


cbar_kws={"shrink": .3 }
if 'heatmap_metrics_per_model_config' in plots_to_make or True:
    tmp_df = df_mean_metrics.copy()
    tmp_df['config'] = tmp_df['config'].apply(lambda x: x.replace('_',':'))
    tmp_df['subject'] = tmp_df['model'].astype(str) + '\n(' + tmp_df['checkpoint'].astype(str) + ')'
    subplots = (
        [ ('overlap_mean', 'overlap_std', subtitles[0])
        , ('kl_mean'     , 'kl_std'     , subtitles[1])
        ]
    )

    # Process Average/STDs
    # Make Heatmaps
    plt.figure()

    # fig, axs = plt.subplots(2, figsize=(36,8), sharex='col', sharey='row', dpi=150)
    # subplots = [(pd.pivot_table(tmp_df, values=column_mean, index=['model', 'checkpoint'], columns=['config'])
    #     , pd.pivot_table(tmp_df, values=column_std, index=['model', 'checkpoint'], columns=['config'])
    #     , title
    #     )
    #     for (column_mean, column_std, title)
    #     in subplots]
    fig, axs = plt.subplots(1,2, figsize=(9.6,20), dpi=150, sharex='col', sharey='row')
    subplots = [(pd.pivot_table(tmp_df, values=column_mean, index=['config'], columns=['subject'])
        , pd.pivot_table(tmp_df, values=column_std, index=['config'], columns=['subject'])
        , title
        )
        for (column_mean, column_std, title)
        in subplots]

    # sns.set_style("whitegrid")
    # fig.suptitle(title)
    # gs = fig.add_gridspec(1, 2, hspace=0, wspace=0)
    for i, (mean_df, std_df, title) in enumerate(subplots):
        cmap = ['Greens', 'Greens_r'][i]

        ax = axs[i]
        ax.set_title(title)
        g = sns.heatmap(mean_df, annot=mean_df, cmap=cmap, linewidths=0.5, ax=ax, annot_kws={'va':'bottom'}, cbar_kws=cbar_kws)
        g.set_xlabel(labels[0])
        g.set_ylabel(labels[1])
        g = sns.heatmap(mean_df, annot=std_df, cmap=cmap, linewidths=0.5, ax=ax, annot_kws={'va':'top'}, cbar=False)
        g.set_xlabel(labels[0])
        g.set_ylabel(labels[1])

    plt.savefig('output/images/metric_mean_std_config_heatmap.png')
    plt.show()

# %% [markdown]
# ### Heatmap + Cat Plot: Metrics per Best Model Configuration

# %%
# Best Config per Model:Checkpoint

title = 'Pontuação Métrica por Modelo - Melhores Configurações'
# subtitles = ['Overlap', 'KL-Divergência']
labels = ['Métrica', 'Pontuação']
metric_types = {
  'Overlap': 'Overlap',
  'KL-Divergence': 'KL-Divergência'
}
metricnames = {
  'bar_pitch_class_histogram': "PCH/Bar",
  'bar_used_pitch': "PC/Bar",
  'total_used_note': "NC",
  'note_length_transition_matrix': "NLTM",
  'pitch_class_transition_matrix': "PCTM",
  'total_used_pitch': "PC",
  'IOI': "IOI",
  'bar_used_note': "NC/Bar",
  'pitch_shift': "PS",
  'pitch_range': "PR",
  'total_pitch_class_histogram': "PCH",
  'note_length_hist': "NLH",
}


# IMPORTANT:
# Determine best configuration for each model:checkpoint
maxes = df_mean_metrics.loc[df_mean_metrics.groupby(['model','checkpoint'])['overlap_mean'].idxmax()]
maxes['seconds_per_bar'] = maxes['time'] / maxes['out_len'] / 10
cols = ['model', 'checkpoint', 'config']
maxes['model_config'] = maxes[cols].apply(lambda row: ':'.join(row.values.astype(str)), axis=1)
maxes.to_pickle(output('df_best_configs'))
maxes.set_index('model_config', drop=True)
# maxes = maxes.rename(columns=metricnames)
maxes['config'] = maxes['config'].apply(lambda x: x.replace('_',':'))
maxes['model_config'] = maxes[cols].apply(lambda row: '\n'.join(row.values.astype(str)), axis=1)
maxes = maxes.drop(columns=['model','checkpoint','in_len','iteration'])

subplots = (
    [ ('_overlap', 'Best Model Configuration: Metric Overlap against Dataset')
    , ('_kl_div', 'Best Model Configuration: Metric KL-Divergence against Dataset')
    ]
)

# Convert DataFrame to Long-Form, splitting by metric type (Overlap / KL-Divergence)
metrics = [metric for metric in maxes.columns for (suffix,_) in subplots if metric.endswith(suffix)]
maxes = maxes[['model_config'] + metrics]
maxes = maxes.melt(id_vars=["model_config"], var_name="metric", value_name="score").dropna()
maxes['metric_type'] = maxes['metric'].astype(str).str.contains(subplots[0][0]).apply(lambda x: 'Overlap' if x == True else 'KL-Divergence')
maxes['metric'] = filter_metric_names(maxes['metric'])
maxes['metric'] = maxes['metric'].apply(lambda x: metricnames[x])


# Best Config of Each - Scatter Plot
# sns.set_theme(style="darkgrid")
sns.set_style(style="whitegrid")
tmp_df = maxes.copy()
tmp_df['metric_type'] = tmp_df['metric_type'].apply(lambda t: metric_types[t])
# tmp_df.rename(columns=metricnames)
g = sns.catplot(data=tmp_df, s=7, y="metric", x="score", hue="model_config", col='metric_type',  kind="swarm", height=4.5, aspect=0.8,
order=maxes.metric.value_counts().index)
locs, labels_ = plt.xticks()
g.set_xticklabels(labels_)
g.set_titles('{col_name}')
plt.xlim(0,1)
# g.fig.suptitle('Metric Performance per Model - Best Configuration of Each')


g.fig.subplots_adjust(top=0.88,wspace=0.2)
g.fig.set_dpi(160)
# g.fig.set_label('Modelo')
# g.set_ylabels(labels[0])
# g.set_xlabels(labels[1])
g.set_ylabels('')
g.set_xlabels('')
plt.tight_layout()
sns.move_legend(
    g, "upper center",
    # bbox_to_anchor=(0.5, -0.1), ncol=4, frameon=False,
    bbox_to_anchor=(0.5, 1.3), ncol=4, frameon=False,
    title="Modelo"
)
dirname = figure_output('best-config-of-each-scatter-plot')
print(dirname)
plt.savefig(dirname, bbox_inches='tight')
plt.show()

# %% 
# ### Heatmap per metric
# title = 'Metric Performance per Model - Best Configuration of Each'
title = 'Pontuação Métrica por Modelo - Melhores Configurações'
labels = ['Métrica', 'Modelo']
metric_types = {
  'Overlap': 'Overlap',
  'KL-Divergence': 'KL-Divergência'
}

# Best Config of Each - Heatmaps
fig, axs = plt.subplots(2, figsize=(10.5,4), sharex='col', sharey='row', dpi=120)
# fig.suptitle(title)
gs = fig.add_gridspec(2, 1, hspace=0, wspace=0)
for i, metric_type in enumerate(reversed(maxes['metric_type'].unique())):
    ax = axs[i]
    ax.set_title(f'{metric_type}')
    cmap = ['Greens', 'Greens_r'][i]
    tmp_df = maxes.copy()
    tmp_df['metric_type'] = tmp_df['metric_type'].apply(lambda t: metric_types[t])
    tmp_df = tmp_df.groupby('metric_type').get_group(metric_types[metric_type])
    tmp_df['model_config'] = tmp_df['model_config'].apply(lambda x: '\n'.join(x for i, x in enumerate(x.split('\n')) if i != 1))
    tmp_df = pd.pivot_table(tmp_df, values='score', index=['model_config'], columns=['metric'])
    g = sns.heatmap(data=tmp_df, ax=axs[i], annot=True, cmap=cmap)
    # g.legend('Modelo')
    # g.set_xlabel(labels[0])
    g.set_xlabel(None)
    # g.set_ylabel(labels[1])
    g.set_ylabel(None)
    ax.legend(loc='center left',fontsize='small', frameon=False)
plt.tight_layout()
plt.savefig(figure_output('best-config-of-each-heatmap'))
plt.show()

# %% [markdown]
# ### Heatmap per Metric

# %%
# Initialize DF
import re

title = 'Overlap Métrico por Modelo-Configuração'
# title = "Overall Metric Overlap per Model Configuration"
labels = ['Pontuação', 'Configuração']

tmp_df = df_mean_metrics.copy()
tmp_df['subject'] = tmp_df[['model', 'checkpoint']].apply(lambda row: ':'.join(row.values.astype(str)), axis=1)

# Define which metrics to plot and subplot arrangement
overlaps = [m for m in metrics if m.endswith('_overlap')]
col_count = 3
row_count = math.ceil(len(overlaps) / col_count / 2)


# Make Plots
# fig, axs = plt.subplots(row_count, col_count, figsize=(16, 40), sharex='col', sharey='row', dpi=120)
# fig, axs = plt.subplots(row_count, col_count, figsize=(40,16), sharex='col', sharey='row', dpi=120)


def plotheatmaps(list_of_overlaps, figname):
  fig, axs = plt.subplots(row_count, col_count, figsize=(11, 20), sharex='col', sharey='row', dpi=120)
  sns.set_theme(style="darkgrid")
  for i, plotcol in enumerate(list_of_overlaps):
      data = tmp_df[['subject', 'config', 'time', plotcol]]
      # data['subject'] = data['subject'].apply(lambda x: x.replace(':', '\n'))
      data['subject'] = data['subject'].apply(lambda x: x.split(':')[0])
      data['config'] = data['config'].apply(lambda x: x.replace('_', ':'))
      data = data.drop(columns='time')
      
      # Generate Plot
      locs, labels_ = plt.xticks()

      sns.set_theme(style="darkgrid")
      # ax = axs[i]
      ax = axs[math.floor(i/col_count), i%col_count]
      
      # Heatmap version
      cmap = ['Greens', 'Greens_r'][0]
      # data = pd.pivot_table(data, values=[plotcol], index=['subject'], columns=['config'])
      labels_ = data['subject'].unique()
      data = pd.pivot_table(data, values=[plotcol], index=['config'], columns=['subject'])
      g = sns.heatmap(data, annot=data, linewidths=0.5, ax=ax, cmap=cmap,
          # cbar_ax=None if i else cbar_ax,
          # cbar= i % col_count == col_count - 1,
          cbar=False,
          vmin=0, vmax=1)

      # labels_ = [':'.join(re.split('_|-', l.get_text())[-2:]) for l in labels_]

      subtitle = '_'.join(re.split('_',plotcol)[:-1])
      subtitle = metricnames[filter_metric_names([subtitle])[0]]
      ax.set_title(subtitle)
      # ax.set_ylabel(labels[0])
      ax.set_ylabel(None)
      ax.set_xlabel(None)
      # ax.set_xlabel(labels[0])
      # if i + 1 == len(overlaps):
          # for l in labels_:
            # l.set_text()
          # labels_ = [':'.join(l.split('_')[-2]) for l in labels_]
      g.set_xticklabels(labels_, rotation=90)
          # ax.set_xlabel(labels[1])
      # else:
          # ax.set(xlabel=None)

  handles, labels_ = ax.get_legend_handles_labels()
  plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
  # plt.title(None)
  # plt.suptitle(title)
  # plt.tight_layout()
  # fig.tight_layout(rect=[0.03, 0, 1, 0.97])
  fig.tight_layout()
  # plt.savefig(figure_output('best-config-mean-metrics-lineplot'))
  plt.savefig(figure_output(figname))
  plt.show()

plotheatmaps(overlaps[:6], 'best-config-mean-metrics-heatmap-1-2')
plotheatmaps(overlaps[6:], 'best-config-mean-metrics-heatmap-2-2')

# %% [markdown]
# ### Point Plot: Best Config vs Baseline per Model

# %%
# Build comparative DataFrame

df_baseline = pd.read_pickle('output/df_metrics_baseline')

# Prepare "best configs" dataframe to receive baselines
df_comp = maxes.copy()
df_comp['model_config'] = df_comp['model_config'].apply(lambda x: x.replace('\n', ':'))
df_comp['config'] = df_comp['model_config'].apply(lambda config: config.split(':')[-2])
df_comp['subject'] = df_comp['model_config'].apply(lambda config: ':'.join(config.split(':')[:-2]))
df_comp = df_comp.drop(columns=['model_config'])

df_baseline['subject'] = df_baseline['model'] + ':' + df_baseline['checkpoint']
df_baseline = df_baseline.drop(columns=['model','checkpoint','dataset'])

df_baseline = df_baseline.melt(id_vars=["subject"], var_name="metric", value_name="score").dropna()
df_baseline['metric_type'] = df_baseline['metric'].astype(str).str.contains('_overlap').apply(lambda x: 'Overlap' if x == True else 'KL-Divergence')
df_baseline['metric'] = filter_metric_names(df_baseline['metric'])
df_baseline['metric'] = df_baseline['metric'].apply(lambda x: metricnames[x])

df_comp_bk = df_comp.copy()
df_comp = df_comp.merge(df_baseline, how='inner', on=['subject', 'metric', 'metric_type'], suffixes=("_gen", "_baseline"))

# Split baseline/generated sample scores
df_comp = df_comp.melt(id_vars=["subject", "metric", "metric_type", "config"], var_name="source", value_name="score").dropna()

# Split metric scores by type (KL-Divergence / Overlap)
df_comp = df_comp.pivot_table(index=['subject','metric', 'source', 'config'], columns='metric_type')
df_comp.columns = df_comp.columns.droplevel().rename(None)
# df_comp.columns = df_comp.columns.droplevel()
df_comp['KL-Divergence'] = df_comp['KL-Divergence'].astype(float)
df_comp['Overlap'] = df_comp['Overlap'].astype(float)
df_comp = df_comp.reset_index()


# %%
# Plot comparison

from plotnine import ggplot, geom_point, aes,geom_line, theme, facet_wrap
from plotnine import ggsave, theme_classic, theme_bw, ggtitle, element_rect
from plotnine import guides, guide_legend, element_text
from math import ceil

title = 'Comparação entre Geração Dinâmica e Estática'
source_colname = 'Geração'
renamer = { 'score_baseline': 'Estática', 'score_gen': 'Dinâmica' }


# df_comp = df_comp[['subject', 'metric', 'source', 'KL-Divergence', 'Overlap']]
data = df_comp.copy()
data['source'] = data['source'].apply(lambda x: renamer[x])
data['subject'] = data['subject'].apply(lambda x: x.split(':')[0])
data = data.rename(columns={ 'source': source_colname, 'metric': 'Métrica', 'KL-Divergence': "KL-Divergência" })


# data['source'] = data['source'].apply(lambda x: )
# data[source_colname] = data[source_colname].apply(lambda x: )
subjects = len(df_comp['subject'].unique())
subjects
p = (
    ggplot(data)
    + facet_wrap(['subject'])
    + geom_line(aes(group='Métrica', x="KL-Divergência", y='Overlap', color='Métrica'), size=0.5)
    + geom_point(aes(shape=source_colname, color='Métrica', x="KL-Divergência", y='Overlap'), size=4)
    + theme_bw()
    + guides(color=guide_legend(ncol=6))
    # + theme(panel_background=element_rect(fill='#ececec'))
    + theme(figure_size=(10, 8), legend_box='horizontal', legend_position="top", legend_direction="row", strip_text=element_text(size=14), text=element_text(size=14))
    # + ggtitle(title)
)

ggsave(plot = p, filename = 'scatterplot_comparison_against_baseline', path=output('images'))
p

# %% [markdown]
# ## Qualitative Analysis

# %%

# Common Dataframe: source, dataset, modelname, checkpoint, filename
filecols = ['source', 'dataset', 'model', 'checkpoint', 'filename']

model_dataset_table = pd.read_pickle('output/df_metrics_baseline')[['model','dataset']]

from analysis_scripts import cmd_convert


# Baseline Samples: Prepare DataFrame
baselinedir = lambda *args: os.path.join(preprocessed_dir, 'baseline', *args)
df_samples_baseline = [[':'.join(['baseline',baseline_model,baseline_checkpoint]), None, baseline_model, baseline_checkpoint, baselinedir(baseline_model, baseline_checkpoint, samplename)]
    for baseline_model in os.listdir(baselinedir())
    for baseline_checkpoint in os.listdir(baselinedir(baseline_model))
    for samplename in os.listdir(baselinedir(baseline_model, baseline_checkpoint) )
]
df_samples_baseline = pd.DataFrame(df_samples_baseline, columns=filecols)
# df_samples_baseline = df_samples_baseline.join(model_dataset_table, on='model')
# TODO: Add dataset info (?)


# Generated Samples (Best Configs Only): Prepare DataFrame
df_samples_generated = pd.read_pickle(output('df_gen'))
df_tmp = pd.read_pickle(output('df_best_configs'))[['model', 'checkpoint', 'config']]
# df_tmp[['in_len', 'out_len']] = df_tmp['config'].astype(str).apply(lambda x: x.split('_'))
df_tmp['in_len'] = df_tmp['config'].astype(str).apply(lambda x: x.split('_')[0]).astype(int)
df_tmp['out_len'] = df_tmp['config'].astype(str).apply(lambda x: x.split('_')[1]).astype(int)
# df_tmp = df_tmp.reset_index()

df_samples_generated = pd.read_pickle(output('df_gen'))
df_samples_generated = df_samples_generated[['model', 'checkpoint', 'dataset', 'out_file', 'in_len', 'out_len', 'out_file_prep']]
df_samples_generated = df_samples_generated.merge(df_tmp, how='inner', on=['model', 'checkpoint', 'in_len', 'out_len'])
df_samples_generated['filename'] = os.path.join(preprocessed_dir, 'generation') + '/' + df_samples_generated['out_file_prep'].astype(str)
df_samples_generated['source'] = 'generated:' + df_samples_generated['model'] + ':' + + df_samples_generated['checkpoint']
df_samples_generated = df_samples_generated[filecols]

# Dataset: Prepare DataFrame
# df_samples_dataset = pd.read_pickle('output/df_dataset_features')
df_samples_dataset = [('dataset:' + dataset, dataset, None, None, output(preprocessed_dir, 'dataset', dataset,filename))
        for dataset in os.listdir(output(preprocessed_dir, 'dataset'))
        for filename in os.listdir(output(preprocessed_dir, 'dataset', dataset))]
df_samples_dataset = pd.DataFrame(df_samples_dataset, columns=filecols)


# Concatenate DataFrames
df_qa_files = pd.concat([df_samples_baseline, df_samples_generated, df_samples_dataset])

# Sample Each Set
df_qa_files = df_qa_files.groupby(['source']) # Group by model:checkpoint
df_qa_files = df_qa_files.apply(pd.DataFrame.sample, random_state=qa_samples_random_state, n=2) 
df_qa_files = df_qa_files.reset_index(drop=True)
df_qa_files['samplename'] = df_qa_files['source'].astype(str) + '_' + df_qa_files.index.astype(str)
df_qa_files

# df_qa_files = df_qa_files
# print(df_qa_files)

# Copy Samples
samplelist = df_qa_files[['filename', 'samplename']].values.tolist()
samplelist
t = tqdm(samplelist)
for filename, samplename in t:
    # cmd = cmd_convert(filename, output('qualitative_analysis', samplename))
    cmd_convert(filename, output('qualitative_analysis', samplename))
    # t.set_description(' '.join(cmd))
    # t.write('\n')
    # t.write(filename)
    # t.write('\n')
    # subprocess.call(cmd)



# # Rename all files
# files = os.listdir(output('qualitative_analysis'))
# random.shuffle(files)

# for i, filename in enumerate(files): print(i, filename)

# %% [markdown]
# # Debug
# ---

# %%
# def get_generation_command(the_modelname, the_checkpointname, output_tracks, datapath, primer, bars_input, bars_output, count)

# primer_length -= 1
# sample_length = 4

print(f'max_input_bars: {max_input_bars}')
print(f'max_output_bars: {max_output_bars}')
print(f'sample_length: {sample_length}')
print(f'primer_length: {primer_length}\n')

a = get_generation_command('melody_rnn', 'attention_rnn', None, 'dataset', 'testprimer', 3, 3, 1)
print(a)


# %%
# Restore #2
import pandas as pd
import os

out_file = os.listdir(f'output/{generation_path}')
def parsefile(line):
    split = line.split('-')
    first_terms = split[:5]
    primer = len('-'.join(first_terms))
    primer = line[primer+1:]
    return first_terms + [generation_path + '/' + line, primer]

out_file = [parsefile(out) for out in out_file]

df_gen = pd.DataFrame(out_file, columns=['model', 'checkpoint', 'iteration', 'in_len', 'out_len', 'out_file', 'primer'])
dff = pd.read_pickle('output/df_gen_bk_2021_09_09').drop(columns=['iteration', 'primer']).drop_duplicates()
df_gen = df_gen.merge(dff, how='inner', on=['model','checkpoint'])
df_gen = df_gen.drop_duplicates()

# df_gen.to_pickle('output/df_gen')
#  df_gen.to_pickle(output('df_gen'))
df_gen.head()
# len(df_gen.values)
# out_file


# %%
# Make the Comparison Table (CSV)
# pd.DataFrame(output_rows, columns=cols_gen).to_pickle(output('df_gen'))
# pd.DataFrame(output_rows, columns=cols_gen)
df = df_comp.copy()
df['source'] = df['source'].apply(lambda x: {'score_baseline': 'Estática', 'score_gen': 'Dinâmica'}[x])
df = df.pivot_table(index=['metric'], columns=['subject','source']).round(3)
df.to_pickle(output('df_final_comparison'))
df.to_csv(output('df_final_comparison.csv'))