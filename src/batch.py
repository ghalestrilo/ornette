from time import sleep
from args import get_batch_args
from batch_client import BatchClient
from features import get_features
from mido import MidiFile

def test_feature_extraction(filename):
    get_features(MidiFile(filename))

def get_filename(expname,index):
  return f'{expname}-promptname-{index}'

def run_experiments(): 
  # prompt = 'dataset/vgmidi/labelled/midi/Super Mario_N64_Super Mario 64_Dire Dire Docks.mid'
  # prompt = 'output/prompt1.mid'
  prompt = 'output/prompt2.mid'


  args = get_batch_args()

  # FIXME: Remove this
  # test_feature_extraction(prompt)
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
      
      if (args.skip_generation == False):
        for i in range(0,args.iterations):
            print(f'[guess] Iteration {i}')
            client.set('buffer_size', i*args.block_size)
            client.reset()
            client.start()

            client.wait()

            client.pause()
            client.debug('history')
            client.debug('output_data')
            client.save(get_filename('guess',i)) # TODO: Update promptname
            # load (create function, cropping to buffer_size)
      
      for i in range(0,args.iterations):
        get_features(MidiFile(get_filename('guess',i)))

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