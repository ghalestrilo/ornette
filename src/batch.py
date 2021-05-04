from time import sleep
from args import get_batch_args
from batch_client import BatchClient
from features import get_features
from mido import MidiFile

from datetime import date
from time import time
from os import path, mkdir, listdir, environ

# Main 
def run_experiments(): 
  expname = ''

  # TODO: Load primers from file/directory
  primers = ['primer1']

  args = get_batch_args()
  print(args)
  
  # Folder and File Names
  basefoldername = str(date.today())
  primerdir = path.join(path.curdir,'dataset','primers')

  i = 0
  while True:
      foldername = f'{basefoldername}-{args.modelname}-{i}'
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

  client = BatchClient(log,args.ip, args.port, args.port_in)

  if (not args.interactive):
    client.wait()
    client.set('debug_output', False)
  else: log("\n\nInteractive mode\n\n")

  # TODO: Automate this

  log(f'Starting experiment suite: {get_output_dir()}/{foldername}')

  # EXPERIMENT BLOCK
  try:
    client.set('batch_mode', True)
    client.set('trigger_generate', 1)
    client.set('batch_unit', 'measures')

    # EXPERIMENT 1: Free improv test
    if args.experiment in ['all', 'free']:
      expname = 'free'
      log(f'Running experiment with model: {args.modelname}')
      if (args.skip_generation == False):
        for i in range(0,args.iterations):
            log(f'Iteration {i}')
            client.reset()
            client.set('buffer_length', (1 + i) * args.block_size)

            client.generate(1, 'measures')
            client.save(get_filename(expname,i))
      
      for i in range(0, args.iterations):
        midi_filename = get_midi_filename(expname, i)

        if not path.exists(midi_filename):
          log(f"fatal: midi file not found ({midi_filename})")
          exit(1)

        # log(f"Extracting features from file: {midi_filename}")
        df = get_features(MidiFile(midi_filename))
        save_df(df, get_pickle_filename(expname, i))
        

    # EXPERIMENT 2: Output precision based on primer length
    if args.experiment in ['all', 'cond-primer']:
      expname = 'cond-primer'
      bars_output = 4  # vary output length
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

    # EXPERIMENT 3: Output precision based on requested output length
    if args.experiment in ['all', 'cond-length']:
      expname = 'cond-length'
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

    
  except KeyboardInterrupt:
    print("Terminating...")
    client.pause()
    if (not args.interactive): client.end()
    exit(1)
  finally:
    if (not args.interactive): client.end()