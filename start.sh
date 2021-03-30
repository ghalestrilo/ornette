#!/bin/bash

server_port="5005"
modelname="$1"
checkpoint_name="$2"
checkpoint_dir="$HOME/.ornette/checkpoints/$modelname"
modulesdir="$(pwd)/modules"
modeldir="$modulesdir/$modelname"
dockerfile="${modeldir}/Dockerfile"
imagename="ornette_$modelname"

# Validations
# TODO: add docker as requirement
# TODO: check that ~/.ornette exists
[ ! $modelname ] && echo "No model provided" && exit

[ ! -d "$checkpoint_dir" ] && mkdir -p $checkpoint_dir

function build_image(){
  docker image remove "$imagename" --force
  [ ! -e "${modeldir}/Dockerfile" ] && echo "Image $imagename not found and $modelname has no Dockerfile" && exit
  docker build -t "$imagename" "$modeldir"
}

# Assert that model container image exists
docker image inspect $imagename > /dev/null;
if [ $? = 1 ]; then build_image
elif [ $REBUILD ]; then build_image
fi

# FIXME: See if it isn't enough to just load a volume "modules/$modelname:/model"
ornette_start_command="bash"

# [ $checkpoint_name ] && ornette_start_command="python server.py --module=$modelname --checkpoint=$checkpoint_name;"

ornette_start_command="python server.py --module=$modelname --checkpoint=$checkpoint_name"

[ $DEV ] && ornette_start_command="alias start=\"$ornette_start_command\"; bash"

docker run -it \
  --hostname server \
  --net=host \
  --device /dev/nvidia0:/dev/nvidia0  \
  --device /dev/nvidiactl:/dev/nvidiactl \
  --device /dev/nvidia-uvm:/dev/nvidia-uvm \
  -v "$(pwd)":/ornette \
  -v "$modeldir":/model \
  -v "$HOME/.ornette/checkpoints/$modelname":/ckpt \
  $imagename bash -c \
  "$ornette_start_command"