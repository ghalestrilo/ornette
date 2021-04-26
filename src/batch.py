from time import sleep
from args import get_batch_args
from batch_client import BatchClient
from features import get_features
from mido import MidiFile

from datetime import date
from time import time
from os import path, mkdir, listdir


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
  return path.normpath(f"{foldername}/{expname}-promptname-{index}")

def get_output_dir():
  
  return path.join(path.curdir,'output')

def get_midi_filename(expname,index):
  return path.join(get_output_dir(), f'{get_filename(expname,index)}.mid')

def get_pickle_filename(expname,index):
  return path.join(get_output_dir(), f'{get_filename(expname,index)}.pkl')

def save_df(df, filename):
    print(f'Saving dataframe to {filename}')
    df.to_pickle(filename)




# Main 
def run_experiments(): 
  # prompt = 'dataset/vgmidi/labelled/midi/Super Mario_N64_Super Mario 64_Dire Dire Docks.mid'
  # prompt = 'output/prompt1.mid'
  prompt = 'output/prompt1.mid'

  args = get_batch_args()

  # FIXME: Remove this
  # get_features(prompt)
  # return
  # /FIXME: Remove this

  client = BatchClient(args.ip, args.port, args.port_in)

  # TODO: Automate this

  # EXPERIMENT BLOCK
  try:
    # EXPERIMENT 1: Guess test
    if (args.experiment in ['all', 'guess']):
      print(f'[guess] Running experiment with model: ...')
      client.set('batch_mode', True)
      client.set('trigger_generate', 1)
      # client.set('debug_output', False)
      
      if (args.skip_generation == False):
        for i in range(0,args.iterations):
            print(f'[guess] Iteration {i}')
            client.set('buffer_length', (1 + i) * args.block_size)
            client.reset()
            client.start()

            client.wait()

            client.pause()
            client.debug('history')
            client.debug('output_data')
            client.save(get_filename('guess',i))
            # load (create function, cropping to buffer_size)
      
      for i in range(0, args.iterations):
        midi_filename = get_midi_filename("guess", i)
        pickle_filename = get_pickle_filename("guess", i)

        print("get_midi_filename: {}".format(midi_filename))
        print("get_pickle_filename: {}".format(pickle_filename))
        print("{} exists: {}".format(
          midi_filename,
          path.exists(midi_filename)
          ))

        print(f'{get_output_dir()}/{foldername} exists: {path.exists(path.join(get_output_dir(),foldername))}')

        if not path.exists(midi_filename):
          print(f"fatal: midi file not found ({midi_filename})")
          exit(1)

        print(f"Extracting features from file: {midi_filename}")
        df = get_features(MidiFile(midi_filename))
        save_df(df, get_pickle_filename("guess", i))
        


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

  except KeyboardInterrupt:
    print("Terminating...")
    client.pause()
    exit(1)