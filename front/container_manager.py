import docker
from requests.exceptions import HTTPError
from docker.errors import NotFound
from threading import Thread
import os
client = docker.from_env()

IMAGE_BASE = "ornette/base"
IMAGE_CLIENT = "ornette/client"
# IMAGE_BATCH_RUNNER="ornette/batch-runner"
# DOCKER_START="docker run -it"

server_port = "5005"
modelname = "$1"
checkpoint_name = "$2"
checkpoint_dir = "$HOME/.ornette/checkpoints/$modelname"
modulesdir = os.path.join(os.curdir, 'modules')
modeldir = f"{modulesdir}/{modelname}"
dockerfile = f"{modeldir}/Dockerfile"

imagename = "ornette_$modelname"
ornette_base_command = "python /ornette"

def build_image(module):
    tag = f'ornette/{module}'
    client.images.remove(tag, force=True)
    if module == 'base':
        img = client.images.build(
            tag=tag, path=os.path.join(os.curdir, 'Dockerfile.base'))
    elif module == 'client':
        img = client.images.build(
            tag=tag, path=os.path.join(os.curdir, 'Dockerfile.client'))
    else:
        img = client.images.build(tag=tag, path=os.path.join(
            modulesdir, module, 'Dockerfile'))
    return img


def assert_image(module):
    tag = f'ornette/{module}'
    try:
        client.images.get(tag)
    except docker.errors.ImageNotFound:
        build_image(module)


def run_client(options):
  try:
    instance = client.containers.run(
        IMAGE_CLIENT,
        network_mode='host',
        detach=True,
        stream=True,
        # stdin_open=True,
        stdout=True,
        stderr=True,
        tty=True,
        volumes={
            os.path.abspath(os.curdir): {
                'bind': '/ornette', 'mode': 'rw'
            }
        }
    )

    # for line in instance.logs(stream=True):
      # print(line.strip().decode('utf-8'))

    for line in instance.attach(
            # stdin=True,
            stream=True):
        print(line.strip().decode('utf-8'))

  except KeyboardInterrupt:
      instance.kill()
      pass

  if instance and instance.status == 'running':
      instance.kill()
  exit()

def print_logs(stream):
  for line in stream:
      print(line.strip().decode('utf-8'))

def build_run_image_command(options):
  return f'bash -c "python /ornette \
    --module={options.modelname} \
    --checkpoint={options.checkpoint} \
    --exec={options.exec or str("")} \
    {"--no-server=True" if options.no_server else ""}  \
    {"--no-module=True" if options.no_module else ""}" \
    '

def run_image(options, paths, append):
  try:
    instance = client.containers.run(
        f'ornette/{options.modelname}',
        build_run_image_command(options),
        network_mode='host',
        stream=True,
        auto_remove=True,
        detach=True,
        hostname='server',
        volumes={
            paths.get("hostdir"):    {'mode': 'ro', 'bind': '/ornette'},
            paths.get("outdir"):     {'mode': 'rw', 'bind': '/output'},
            paths.get("datasetdir"): {'mode': 'ro', 'bind': '/dataset'},
            paths.get("moduledir"):  {'mode': 'ro', 'bind': '/model'},
            paths.get("ckptdir"):    {'mode': 'rw', 'bind': '/ckpt'},
            paths.get("datadir"):    {'mode': 'ro', 'bind': '/data'}
        }
    )

    for line in instance.logs(stream=True):
      append(line.strip().decode('utf-8'))

  except KeyboardInterrupt:
    try:
      instance.kill()

      if instance and instance.status == 'running':
          instance.kill()
    except (HTTPError, NotFound):
      pass
