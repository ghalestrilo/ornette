#!/bin/bash

server_port="5005"
modelname="$1"
checkpoint_name="$2"
checkpoint_dir="$HOME/.ornette/checkpoints/$modelname"
modulesdir="$(pwd)/modules"
modeldir="$modulesdir/$modelname"
dockerfile="${modeldir}/Dockerfile"
imagename="ornette_$modelname"
# batch_runner_command="python scripts/batch.py"
ornette_base_command="python /ornette"

ORNETTE_BASE="ornette/base"
ORNETTE_CLIENT="ornette/client"
ORNETTE_BATCH_RUNNER="ornette/batch-runner"



# Definitions
function build_image(){
  docker image remove "$imagename" --force
  [ ! -e "${modeldir}/Dockerfile" ] && echo "Image $imagename not found and $modelname has no Dockerfile" && exit
  docker build -t "$imagename" "$modeldir"
}

function build_base_image(){
  docker build -t $ORNETTE_BASE -f Dockerfile.base .
}

function build_client_image(){
  docker build -t $ORNETTE_CLIENT -f Dockerfile.client .
}

function build_batch_runner_image(){
  docker build -t $ORNETTE_BATCH_RUNNER -f Dockerfile.batch_runner .
}



# Validations
# TODO: add docker as requirement
# TODO: check that ~/.ornette exists
[ ! $modelname ] && echo "No model provided (arg 1)" && exit
[ ! $checkpoint_dir ] && echo "No checkpoint provided (arg 2)"

[ ! -d "$checkpoint_dir" ] && mkdir -p $checkpoint_dir



if [ $modelname = 'client' ]; then
  # Assert that ornette client image exists
  docker image inspect $ORNETTE_CLIENT > /dev/null;
  if [ $? = 1 ];          then build_client_image
  elif [ $REBUILD ]; then build_client_image
  fi

  docker run -it \
    --net=host \
    -v "$(pwd)":/ornette \
    $ORNETTE_CLIENT
  exit
fi

if [ $modelname = 'batch' ]; then
  # Assert that ornette client image exists
  docker image inspect $ORNETTE_BATCH_RUNNER > /dev/null;
  if [ $? = 1 ];       then build_batch_runner_image
  elif [ $REBUILD ];   then build_batch_runner_image
  fi

  docker run -it \
    --net=host \
    -e BATCH_RUNNER=1 \
    -v "$(pwd)":/ornette \
    $ORNETTE_BATCH_RUNNER \
    $ornette_base_command
  exit
fi


# Assert that ornette base image exists
docker image inspect $ORNETTE_BASE > /dev/null;
if [ $? = 1 ];          then build_base_image
elif [ $FULL_REBUILD ]; then build_base_image
fi

# Assert that model container image exists
docker image inspect $imagename > /dev/null;
if [ $? = 1 ];          then build_image
elif [ $REBUILD ];      then build_image
elif [ $FULL_REBUILD ]; then build_image
fi


# Start Server

ornette_start_command="python /ornette --module=$modelname --checkpoint=$checkpoint_name"

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