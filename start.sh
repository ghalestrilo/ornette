#!/bin/bash

server_port="5005"
modelname="$1"
modulesdir="modules"
modeldir="$modulesdir/$modelname"
dockerfile="${modeldir}/Dockerfile"
imagename="ornette_$modelname"

# Validations
# TODO: add docker as requirement
# TODO: check that ~/.ornette exists
[ ! $modelname ] && echo "No model provided" && exit



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
# ornette_start_command="cd /ornette && python server.py --model_name=$modelname;"
# ornette_start_command="cd /ornette && bash"
ornette_start_command="bash"

docker run -it \
  --device /dev/nvidia0:/dev/nvidia0  \
  --device /dev/nvidiactl:/dev/nvidiactl \
  --device /dev/nvidia-uvm:/dev/nvidia-uvm \
  -p $server_port:$server_port \
  -p 8080:8080 \
  -v "$(pwd)":/ornette \
  -v "$(pwd)/$modeldir":/model \
  $imagename bash -c \
  $ornette_start_command