import sys
import docker
import threading
from requests.exceptions import HTTPError
from docker.errors import NotFound
from textual.app import App
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from textual.reactive import Reactive
from textual.widget import Widget
from textual.widgets import ScrollView


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

        for line in instance.attach(stream=True):
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
    paths["ckptdir"] = os.path.join(
        paths["datadir"], 'checkpoints', options.modelname)
    paths["hostdir"] = os.path.join(paths["curdir"], 'server')
    paths["outdir"] = os.path.join(paths["curdir"], 'output')
    paths["datasetdir"] = os.path.join(paths["curdir"], 'dataset')
    paths["moduledir"] = os.path.join(
        paths["curdir"], 'modules', options.modelname)
    return paths

def log_append_loop(instance, append, stop):
    for line in instance.logs(stream=True):
          if stop.is_set(): break
          append(line.strip().decode('utf-8'))

def run_image(append, options, stop):
    paths = get_paths(options)
    instance = client.containers.run(
        f'ornette/{options.modelname}',
        build_run_image_command(options),
        network_mode='host',
        stream=True,
        # auto_remove=True,
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

    try:
        for line in instance.logs(stream=True):
            if stop.is_set():
                break
            append(line.strip().decode('utf-8'))
        if instance and instance.status == 'running':
          instance.kill()
    except (HTTPError, NotFound):
        if instance and instance.status == 'running':
            instance.kill()
        pass


import os

class ScrollingTextDisplay(Widget):
    """ Class that runs the MDGS and renders its output """
    docker_thread = None
    stop_flag = threading.Event()
    logs = Reactive([])
    logheight = 13

    def append(self, msg):
        self.logs.append(msg)
        self.refresh()

    async def set_height(self, height):
      self.logheight = max(height - 2, 3)

    def run_image(self, options):
        self.docker_thread = threading.Thread(
            target=run_image, args=[self.append, options, self.stop_flag])
        self.docker_thread.start()

    def render(self):
        height = os.get_terminal_size().lines - 3
        text_to_render = '\n'.join(self.logs[-(height - 1):])
        return Panel(Text(text_to_render), title="output", title_align="left",height=height)

    def stop(self):
        self.stop_flag.set()

    async def on_shutdown_request(self) -> None:
        self.stop()
