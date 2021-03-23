#!/bin/bash

server_port="5005"
modelname="$1"
modeldir="models/$modelname"
dockerfile="${modeldir}/Dockerfile"
imagename="ornette-$modelname"

[ ! $modelname ] && echo "No model provided" && exit

# TODO: add docker as requirement


# Assert that model container image exists
if ! test -z "docker image inspect $imagename"; then
  [ ! -e "${modeldir}/Dockerfile" ] && echo "Image $imagename not found and $modelname has no Dockerfile" && exit
  docker build -t $imagename $modeldir
fi

# FIXME: See if it isn't enough to just load a volume "models/$modelname:/model"
# ornette_start_command="cd /ornette && python server.py --model_name=$modelname;"
ornette_start_command="bash"

docker run -it \
  -p $server_port:$server_port \
  -v $(pwd):/ornette \
  $imagename bash -c \
  $ornette_start_command