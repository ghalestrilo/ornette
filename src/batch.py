from time import sleep
from args import get_batch_args
from batch_client import BatchClient

def run_experiments():
  pass

def run_experiments_(): # FIXME: After testing feature extraction, remove underscore suffix from method name
  args = get_batch_args()

  client = BatchClient(args.ip, args.port, args.port_in)

  # TODO: Automate this
  prompt = 'dataset/vgmidi/labelled/midi/Super Mario_N64_Super Mario 64_Dire Dire Docks.mid'

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
            client.save(f'guess-promptname-{i}') # TODO: Update promptname
            # load (create function, cropping to buffer_size)
      

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