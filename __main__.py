import os
from argparse import ArgumentParser
from front.front import Front
from front.ui import dropdown
from front.container_manager import build_image, run_client


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

def main():

    # TODO: Move to Front.on_mount
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

    front = Front(options)
    front.set_options(options)
    front.run()

# Main
if __name__ == '__main__':
  main()
