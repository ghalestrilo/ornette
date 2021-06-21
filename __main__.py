import docker
from argparse import ArgumentParser
from subprocess import PIPE
import os


server_port="5005"
modelname="$1"
checkpoint_name="$2"
checkpoint_dir="$HOME/.ornette/checkpoints/$modelname"

modulesdir=os.path.join(os.curdir, 'modules')

modeldir=f"{modulesdir}/{modelname}"
dockerfile=f"{modeldir}/Dockerfile"
imagename="ornette_$modelname"
# batch_runner_command="python scripts/batch.py"
ornette_base_command="python /ornette"

IMAGE_BASE="ornette/base"
IMAGE_CLIENT="ornette/client"
# IMAGE_BATCH_RUNNER="ornette/batch-runner"
# DOCKER_START="docker run -it"

client = docker.from_env()


# Command-Line options
args = ArgumentParser()
args.add_argument('--modelname', type=str, help="The improvisation model you want to run")
args.add_argument('--checkpoint', type=str, help="The checkpoint to be loaded")
args.add_argument('--rebuild', type=bool, default=False, help="Force docker images to be rebuilt")
options = args.parse_args()

# Procedures
def build_image(module):
  tag = f'ornette/{module}'
  client.images.remove(tag, force=True)
  if module == 'base':
    img = client.images.build(tag=tag, path=os.path.join(os.curdir, 'Dockerfile.base'))
  elif module == 'client':
    img = client.images.build(tag=tag, path=os.path.join(os.curdir, 'Dockerfile.client'))
  else:
    img = client.images.build(tag=tag, path=os.path.join(modulesdir, module, 'Dockerfile'))
  return img

def assert_image(module):
  tag = f'ornette/{module}'
  try:
    client.images.get(tag)
  except docker.errors.ImageNotFound:
    build_image(module)


if __name__ == '__main__':

  # Choose model
  if options.modelname is None:
    print(os.listdir(modulesdir))
    options.modelname = os.listdir(modulesdir)[0]

  # Check rebuild
  if options.rebuild:
    build_image('base')
    build_image(options.modelname)

  # Run Client
  if options.modelname == 'client':
    client.containers.run(IMAGE_CLIENT,
      network_mode='host',
      volumes={ os.path.abspath(os.curdir): { 'bind': '/ornette', 'mode': 'rw' } })
    exit

  # Choose checkpoint
  if options.checkpoint is None:
    print(os.listdir(modulesdir))
    options.checkpoint = os.listdir(modulesdir)[0]

  # Run Module
  curdir = os.path.abspath(os.curdir)
  for msg in client.containers.run(f'ornette/{options.modelname}',
    network_mode = 'host',
    stream = True,
    command = 'bash -c python /ornette',
    stderr=True,
    hostname = 'server',
    volumes = {
      os.path.join(curdir, 'server'): { 'bind': '/ornette', 'mode': 'ro' },
      os.path.join(curdir, 'output'): { 'bind': '/output', 'mode': 'rw' },
      os.path.join(curdir, 'modules', options.modelname): { 'bind': '/model', 'mode': 'ro' },
      os.path.join(os.path.expanduser('~'), '.ornette', 'checkpoints', options.modelname): { 'bind': '/ckpt', 'mode': 'ro' }
    }
  ):
    print(msg)