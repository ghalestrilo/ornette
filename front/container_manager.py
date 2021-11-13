import docker
from requests.exceptions import HTTPError
from docker.errors import NotFound

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

def build_run_image_command(options):
  return f'bash -c "python /ornette \
    --module={options.modelname} \
    --checkpoint={options.checkpoint} \
    --exec={options.exec or str("")} \
    {"--no-server=True" if options.no_server else ""}  \
    {"--no-module=True" if options.no_module else ""}" \
    '



# Procedures
def get_paths(options):
  paths = {}
  paths["curdir"] = os.path.abspath(os.curdir)
  paths["datadir"] = os.path.join(os.path.expanduser('~'), '.ornette')
  paths["ckptdir"] = os.path.join(paths["datadir"], 'checkpoints', options.modelname)
  paths["hostdir"] = os.path.join(paths["curdir"], 'server')
  paths["outdir"] = os.path.join(paths["curdir"], 'output')
  paths["datasetdir"] = os.path.join(paths["curdir"], 'dataset')
  paths["moduledir"] = os.path.join(paths["curdir"], 'modules', options.modelname)
  return paths

def run_image(queue, options, stop):
    paths = get_paths(options)
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
      queue.put(line.strip().decode('utf-8'))
      if stop.is_set():
        instance.kill()
        break
    instance.kill()










































class ContainerManager():
  def __init__(self, queue, options):
    self.instance = None
    self.engine = None
    self.options = options
    self.queue = queue

    # Define directories
    self.paths = get_paths(options)


  def start(self):
    self.engine = Process(target=self.run_image, args=[])
    self.engine.start()

  def run_image(self):
    paths = self.paths
    options = self.options
    self.instance = client.containers.run(
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

    for line in self.instance.logs(stream=True):
      self.queue.put(line.strip().decode('utf-8'))

  def stop(self):
    try:
      # if self.instance == None: self.engine.join()

      if self.instance and self.instance.status == 'running':
          self.instance.kill()
    except (HTTPError, NotFound):
      pass
    self.engine.join()