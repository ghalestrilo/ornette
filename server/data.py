# TODO: Rename: 'Loader'

# import tensorflow as tf
from importlib import reload
import yaml
import urllib.request as req
import os
import sys

# Data: This module is responsible for managing data stored in the disk
# This includes:
#  - Model Checkpoints
#  - Datasets
#  - Outputs

from os.path import normpath, join
from pathlib import Path

configdir = os.path.join(os.path.expanduser('~'), '.ornette')


def process_options(options, selector_component):
    if options.modelname is None:
        message = "\n Which model do you want to run?"
        directory = 'modules'
        choices = [file for file in os.listdir(
            directory) if os.path.isdir(os.path.join(directory, file))]
        options.modelname = selector_component(message, choices)

    # Check rebuild
    if options.rebuild:
        build_image('base')
        build_image(options.modelname)

    # Run Client
    # if options.modelname == 'client':
        # run_client(options)

    # Choose checkpoint
    options.checkpoint = select_bundle(options, selector_component)
    return options


def select_bundle(options, selector_component):
    modelname = options.modelname
    bundledir = Path(configdir, 'checkpoints', modelname)
    if not bundledir.exists():
        bundledir.mkdir(parents=True)

    if options.checkpoint is not None:
        return options.checkpoint
    message = f"\n Which {modelname} bundle to load?"

    bundles = get_model_bundles(modelname)
    choices = list(bundles.keys())
    if choices == []:
        print(f'Model {modelname} has no bundles to choose from')
        return None
    selection = selector_component(message, choices)

    downloaded = list(bundledir.glob('*'))
    if selection not in downloaded:
      download_checkpoint(modelname, selection, bundles[selection], False)
    
    return selection


def load_folder(name):
    sys.path.append(os.path.join(sys.path[0], name))


def download_checkpoint(modelname, bundlename, url, force=False):
    bundlepath = Path(configdir, 'checkpoints', modelname, bundlename)
    if bundlepath.exists() and not force:
        return
    print(f'downloading {modelname}:{bundlename}, "{url}"')
    response = req.urlopen(url, timeout=5)
    content = response.read()
    with open(bundlepath, 'wb') as f:
        f.write(content)
        f.close()

def get_model_bundles(modelname):
    yml_files = list(Path('modules',modelname).glob('.ornette.y*ml'))
    if yml_files == []:
      print(f"Error: {modelname} has no .ornette.yml file in its folder.")
      exit(1)
      return
    ornette_yml = yml_files[0]
    with open(ornette_yml) as file:
          moduleconfig = yaml.load_all(file, Loader=yaml.FullLoader)
          for pair in moduleconfig:
              for k, v in pair.items():
                  if k == "checkpoints":
                      return v

def load_model(host, checkpoint=None, model_path='/model'):
    if checkpoint is None:
        host.io.log("Please provide a checkpoint for the model to load")
        exit(-1)

    path = os.path.abspath(model_path)
    load_folder(path)
    import ornette
    reload(ornette)
    return ornette.OrnetteModule(host, checkpoint=checkpoint)


def get_bundle(host, bundle_name):
    print(f'module = {host.get("module")}')
    checkpoint_path = [
        host.get('data_dir'), 'checkpoints', host.get('module'), bundle_name]
    checkpoint_path = os.path.join(*checkpoint_path)
    return checkpoint_path
