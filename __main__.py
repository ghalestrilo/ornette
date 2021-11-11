import os
from argparse import ArgumentParser
from multiprocessing import Process, Manager

from front.ui import dropdown, display
from front.container_manager import build_image, assert_image, run_client, run_image

configdir = os.path.join(os.path.expanduser('~'), '.ornette')

# Command-Line options
args = ArgumentParser()
args.add_argument('--modelname', type=str,
                  help="The improvisation model you want to run")
args.add_argument('--checkpoint', type=str, help="The checkpoint to be loaded")
args.add_argument('--rebuild', type=bool, default=False,
                  help="Force docker images to be rebuilt")
args.add_argument('--exec', type=str, default=None,
                  help="Startup command to run on the server")
args.add_argument("--no-server",     type=bool, default=False,        help="Run the model without starting an OSC server")
args.add_argument("--no-module",     type=bool, default=False,        help="Run ornette without a model")
options = args.parse_args()

# Procedures
def get_paths():
  paths = {}
  paths["curdir"] = os.path.abspath(os.curdir)
  paths["datadir"] = os.path.join(os.path.expanduser('~'), '.ornette')
  paths["ckptdir"] = os.path.join(paths["datadir"], 'checkpoints', options.modelname)
  paths["hostdir"] = os.path.join(paths["curdir"], 'server')
  paths["outdir"] = os.path.join(paths["curdir"], 'output')
  paths["datasetdir"] = os.path.join(paths["curdir"], 'dataset')
  paths["moduledir"] = os.path.join(paths["curdir"], 'modules', options.modelname)
  return paths

# Main
if __name__ == '__main__':

    # Choose model
    if options.modelname is None:
        message = "\n Which model do you want to run?"
        directory = 'modules'
        choices = [file for file in os.listdir(
            directory) if os.path.isdir(os.path.join(directory, file))]
        options.modelname = dropdown(message, choices)

    # Check rebuild
    if options.rebuild:
        build_image('base')
        build_image(options.modelname)

    # Run Client
    if options.modelname == 'client':
        run_client(options)

    # Choose checkpoint
    if options.checkpoint is None:
        message = f"\n Which {options.modelname} bundle to load?"
        directory = os.path.join(configdir, 'checkpoints', options.modelname)
        choices = os.listdir(directory)
        options.checkpoint = dropdown(message, choices)

    # Define directories
    paths = get_paths()

    # Run Module
    print(f'\n Starting {options.modelname}:{options.checkpoint}')

    with Manager() as manager:
      engine_output = manager.list()
      # display = DisplayManager(engine_output)

      engine = Process(target=run_image, args=[options, paths, engine_output.append])
      engine.start()

      display_process = Process(target=display, args=[engine_output])
      display_process.start()

      engine.join()
      display_process.join()