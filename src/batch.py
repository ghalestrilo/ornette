from time import sleep
from args import get_batch_args
from batch_client import BatchClient
from features import get_features
from mido import MidiFile

from datetime import date
from time import time
from os import path, mkdir, listdir, environ

sleep(1)

# Main 
def run_experiments(): 
  # prompt = 'dataset/vgmidi/labelled/midi/Super Mario_N64_Super Mario 64_Dire Dire Docks.mid'
  # prompt = 'output/prompt1.mid'
  prompt = 'output/prompt1.mid'
  args = get_batch_args()
  print(args)
  
  # Folder and File Names
  basefoldername = str(date.today())

  i = 0
  while True:
      foldername = f'{basefoldername}-{i}'
      if not path.exists(path.normpath(f'output/{foldername}')):
        mkdir(path.normpath(f'output/{foldername}'))
        break
      i = i + 1

  def get_filename(expname,index):
    return path.normpath(f"{foldername}/{args.modelname}-{expname}-promptname-{index}")

  def get_output_dir():
    
    return path.join(path.curdir,'output')

  def get_midi_filename(expname,index):
    return path.join(get_output_dir(), f'{get_filename(expname,index)}.mid')

  def get_pickle_filename(expname,index):
    return path.join(get_output_dir(), f'{get_filename(expname,index)}.pkl')

  def save_df(df, filename):
      # print(f'Saving dataframe to {filename}')
      df.to_pickle(filename)

  client = BatchClient(args.ip, args.port, args.port_in)

  if (not args.interactive):
    client.wait()
    client.set('debug_output', False)
  else: print("\n\nInteractive mode\n\n")

  # TODO: Automate this

  print(f'[global] Starting experiment suite: {get_output_dir()}/{foldername}')

  # EXPERIMENT BLOCK
  try:
    # EXPERIMENT 1: Guess test
    if (args.experiment in ['all', 'free']):
      expname = 'free'
      print(f'[guess] Running experiment with model: {args.modelname}')
      client.set('batch_mode', True)
      client.set('trigger_generate', 1)
      client.set('batch_unit', 'measures')
      # client.set('debug_output', False)
      
      if (args.skip_generation == False):
        for i in range(0,args.iterations):
            print(f'[guess] Iteration {i}')
            client.reset()
            client.pause()
            client.set('buffer_length', (1 + i) * args.block_size)
            # load (create function, cropping to buffer_size)
            # client.set('missing_measures', 1)

            # client.run(get_filename(expname,i))
            client.generate(1, 'measures')
            client.save(get_filename(expname,i))
            client.wait()
      
      for i in range(0, args.iterations):
        midi_filename = get_midi_filename(expname, i)

        # print("get_midi_filename: {}".format(midi_filename))
        # print("get_pickle_filename: {}".format(pickle_filename))
        # print("{} exists: {}".format( midi_filename, path.exists(midi_filename) ))
        # print(f'{get_output_dir()}/{foldername} exists: {path.exists(path.join(get_output_dir(),foldername))}')

        if not path.exists(midi_filename):
          print(f"fatal: midi file not found ({midi_filename})")
          exit(1)

        # print(f"Extracting features from file: {midi_filename}")
        df = get_features(MidiFile(midi_filename))
        save_df(df, get_pickle_filename(expname, i))
        


    # Algorithm
    # Set batch mode
    # (outer loop) Set prompt 
    # (inner loop) Set buffer size, reset history, set max_output_time
    #     Load, crop Prompt (TODO: load function in host, encode function in model)
    #     Run Model
    #     TODO: Await response? start another server thread?
    # Process Result:
    # Load MIDI using Mido
    # Convert Mido to Pandas (?)
    # Calculate Error (NEED HELP)
    if (not args.interactive): client.end()
  except KeyboardInterrupt:
    print("Terminating...")
    client.pause()
    if (not args.interactive): client.end()
    exit(1)