#!/bin/bash

if pip show virtualenv; then pip install virtualenv; fi

if [ ! -d envs ]; then mkdir envs; fi

for modelname in $(find models -mindepth 1 -maxdepth 1 -type d -exec basename {} \;); do
  path="envs/$modelname"
  if [ -d path ]; then continue; fi
  
  virtualenv "$path"
  source "$path/bin/activate"
  pip install -r "models/$modelname/requirements.txt"
  deactivate
done