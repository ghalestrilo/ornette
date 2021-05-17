from time import sleep
from args import get_batch_args
from batch_client import BatchClient
from features import get_features
from mido import MidiFile

from datetime import date
from time import time
from os import path, mkdir, listdir, environ
import subprocess

args = get_batch_args()

client  = None
server  = None
expname = ''

evaluation_sets = [
  ('bach-chorales', [
    ('polyphony_rnn', 'polyphony_rnn'),
    ('pianoroll_rnn_nade', 'rnn-nade_attn'),
    ('rl_duet', 'rl_duet'),
  ]),
  ('', [
    ('performance_rnn', 'performance_with_dynamics'),
    # ('music_transformer', 'performance_with_dynamics')
  ]),
  ('None', [
    # ('melody_rnn', 'attention_rnn')
  ]),
  ('None', [
    # ('remi', 'remi')
  ])
]

def analysis_input_length(primer):
  pass

def analysis_output_length(primer):
  pass

experiments = [
  ('input_len', analysis_input_length),
  # ('output_len', analysis_output_length)
  ]

def experiment(name, fn):
  expname = name
  result = [fn(primer) for primer in primers]
  for primer in primers:
    for i in range(args.iterations):
      fn(primer)
  # TODO: save pickle








client = BatchClient(log,args.ip, args.port, args.port_in)
def start_model(modelname, checkpointname):
  modelname = modelname
  server = subprocess.Popen([ './start.sh', model, checkpoint ])
  client.wait()
  client.set('debug_output', False)
  client.set('batch_mode', True)
  client.set('trigger_generate', 1)
  client.set('batch_unit', 'measures')
  client.set('debug_output', False)
  pass

def stop_model():
  if client: client.end()
  if server: server.wait()



# TODO: Load primers from file/directory


# Folder and File Names
basefoldername = str(date.today())
primerdir = path.join(path.curdir,'dataset','primers')






i = 0
while True:
    foldername = f'{basefoldername}-{i}'
    if not path.exists(path.normpath(f'output/{foldername}')):
      mkdir(path.normpath(f'output/{foldername}'))
      break
    i = i + 1


# File Management
def get_filename(expname,index,primer=None):
  return path.normpath(
    f"{foldername}/{expname}-{index}"
    if primer is None else
    f"{foldername}/{expname}-{primer}-{index}")

def get_primer_filename(name):
  return path.join(primerdir,f'{name}.mid')

def get_output_dir():
  return path.join(path.curdir,'output')

def get_midi_filename(expname,index,primer=None):
  return path.join(get_output_dir(), f'{get_filename(expname,index,primer)}.mid')

def get_pickle_filename(expname,index,primer=None):
  return path.join(get_output_dir(), f'{get_filename(expname,index,primer)}.pkl')

def save_df(df, filename):
    # log(f'Saving dataframe to {filename}')
    df.to_pickle(filename)

def log(message):
    print(f'[batch:{expname}] {message}')















# EXPERIMENT BLOCK
try:
  log(f'Starting experiment suite: {get_output_dir()}/{foldername}')

  # EXPERIMENT 1: Output precision based on primer length
  if args.experiment in ['all', 'input-len']:
    expname = 'input-len'
    bars_output = 4  # vary output length
    client.set('voices', 1, 2)
    for primer in primers:
      for i in range(args.iterations):
        log(f'iteration: {i}')
        for j in range(1,args.max_bars):
          bars_input = j # Vary input length
          client.reset()
          client.load_bars(get_primer_filename(primer), bars_input)
          for b in range(bars_output): client.generate(1, 'measures')
          filename = get_filename(expname,i,f'{primer}-{j}-bars')
          log(f'save output to: {filename}')
          client.save(filename)

  # EXPERIMENT 2: Output precision based on requested output length
  if args.experiment in ['all', 'output-len']:
    expname = 'output-len'
    bars_input = 4 # Fixed input length
    for primer in primers:
      for i in range(args.iterations):
        log(f'iteration: {i}')
        for j in range(1,args.max_bars):
          bars_output = j # Vary output length
          client.reset()
          client.load_bars(get_primer_filename(primer), bars_input)
          for b in range(bars_output): client.generate(1, 'measures')
          filename = get_filename(expname,i,f'{primer}-{j}-bars')
          log(f'save output to: {filename}')
          client.save(filename)


  for dataset, models in evaluation_sets:
    datapath = path.join('datasets', dataset)
    if not path.exists(datapath):
      print(f'Directory not found: {datapath}, skipping')
      continue

    primers = listdir(datapath)

    for (model, checkpoint) in models:
      start_model(model, checkpoint)

      for name, exp in experiments:
        experiment(name, exp)

      stop_model()

except KeyboardInterrupt:
  print("Terminating...")
  client.pause()
finally:
  client.end()