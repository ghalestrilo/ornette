import docker
from argparse import ArgumentParser
from subprocess import PIPE
import os

from bullet import Bullet
from bullet import colors


server_port = "5005"
modelname = "$1"
checkpoint_name = "$2"
checkpoint_dir = "$HOME/.ornette/checkpoints/$modelname"

modulesdir = os.path.join(os.curdir, 'modules')

modeldir = f"{modulesdir}/{modelname}"
dockerfile = f"{modeldir}/Dockerfile"
imagename = "ornette_$modelname"
# batch_runner_command="python scripts/batch.py"
ornette_base_command = "python /ornette"

IMAGE_BASE = "ornette/base"
IMAGE_CLIENT = "ornette/client"
# IMAGE_BATCH_RUNNER="ornette/batch-runner"
# DOCKER_START="docker run -it"

configdir = os.path.join(os.path.expanduser('~'), '.ornette')

client = docker.from_env()


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
options = args.parse_args()

# Procedures


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


def dropdown(prompt, choices):
    cli = Bullet(
        prompt=prompt,
        choices=choices,
        indent=0,
        align=5,
        margin=2,
        bullet=">",
        bullet_color=colors.bright(colors.foreground["yellow"]),
        word_on_switch=colors.bright(colors.foreground["yellow"]),
        background_on_switch=colors.background["black"],
        pad_right=2
    )
    return cli.launch()


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

    # Choose checkpoint
    if options.checkpoint is None:
        message = f"\n Which {options.modelname} bundle should be loaded?"
        directory = os.path.join(configdir, 'checkpoints', options.modelname)
        choices = os.listdir(directory)
        options.checkpoint = dropdown(message, choices)

    # Define directories
    curdir = os.path.abspath(os.curdir)
    ckptdir = os.path.join(os.path.expanduser(
        '~'), '.ornette', 'checkpoints', options.modelname)
    hostdir = os.path.join(curdir, 'server')
    outdir = os.path.join(curdir, 'output')
    datadir = os.path.join(curdir, 'dataset')
    moduledir = os.path.join(curdir, 'modules', options.modelname)

    # Run Module
    print(f'\n Starting {options.modelname}:{options.checkpoint}')
    try:
        instance = client.containers.run(
            f'ornette/{options.modelname}',
            f'bash -c "python /ornette \
          --module={options.modelname} \
          --checkpoint={options.checkpoint} \
          --exec={options.exec or str("")} \
          {"--no-server=True" if options.no_server else ""}" \
          ',
            network_mode='host',
            stream=True,
            auto_remove=True,
            detach=True,
            hostname='server',
            volumes={
                hostdir:   {'mode': 'ro', 'bind': '/ornette'},
                outdir:    {'mode': 'rw', 'bind': '/output'},
                datadir:   {'mode': 'ro', 'bind': '/dataset'},
                moduledir: {'mode': 'ro', 'bind': '/model'},
                ckptdir:   {
                     'mode': 'rw', 'bind': '/ckpt'}
            }
        )

        for line in instance.logs(stream=True):
            print(line.strip().decode('utf-8'))
    except KeyboardInterrupt:
        instance.kill()

    if instance and instance.status == 'running':
        instance.kill()
