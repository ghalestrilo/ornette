#!/bin/bash

if ! pip show virtualenv; then pip install virtualenv; fi

if [ ! -d envs ]; then mkdir envs; fi

for modelname in $(find models -mindepth 1 -maxdepth 1 -type d -exec basename {} \;); do
  envpath="./envs/$modelname"
  [ -d "$envpath" ] && continue;
  
  virtualenv "$envpath"
  source "$envpath/bin/activate"
  pip install --upgrade pip
  pip install -r "models/$modelname/requirements.txt"
  deactivate
done