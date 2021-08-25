# TODO: Rename: 'Loader'

# import tensorflow as tf
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

def load_folder(name):
    sys.path.append(os.path.join(sys.path[0], name))


def download_checkpoint(name, url, force=False):
    checkpoint_dir = '/ckpt'
    ckptpath = normpath(f'{checkpoint_dir}/{name}')
    if os.path.exists(ckptpath) and not force:
        return
    print(f'downloading  {name}, "{url}"')
    response = req.urlopen(url, timeout=5)
    content = response.read()
    with open(ckptpath, 'wb') as f:
        f.write(content)
        f.close()


def prep_module():
    with open(normpath('/model/.ornette.yml')) as file:
        moduleconfig = yaml.load_all(file, Loader=yaml.FullLoader)
        for pair in moduleconfig:
            for k, v in pair.items():
                if k == "checkpoints":
                    for checkpoint_name, checkpoint_url in v.items():
                        print(f'checking {checkpoint_name}')
                        download_checkpoint(
                            checkpoint_name, checkpoint_url, False)
                # if verbose: print(k, ' -> ', v)

from importlib import reload

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
  checkpoint_path = [host.get('data_dir'), 'checkpoints', host.get('module'), bundle_name]
  checkpoint_path = os.path.join(*checkpoint_path)
  return checkpoint_path







