#!/bin/bash
# docker run -it -e "TERM=xterm-256color" -v $(pwd):/ornette ornette/melody_rnn  bash -c "python -m unittest tests/filters/test_magenta.py; python -m unittest tests/test_models.py"
docker run -it -e "TERM=xterm-256color" \
  -v $(pwd):/ornette \
  -v $HOME/.ornette:/data \
  -v $HOME/.ornette/checkpoints:/checkpoints \
  -v $HOME/.ornette/checkpoints/melody_rnn:/ckpt \
  ornette/melody_rnn \
  bash -c "python -m unittest tests.models.test_magenta.TestModelGeneration.test_repeated_generation --failfast"
  # bash -c "python -m unittest tests/models/test_magenta.py --failfast"
  # bash -c "python -m unittest tests/models/test_magenta.py"
  # bash -c "python -m unittest tests.models.test_magenta.TestModelGeneration.test_repeated_generation_no_extra_end_of_track --failfast"
  # bash -c "python -m unittest tests.models.test_magenta.TestModelGeneration.test_repeated_generation_end_of_track --failfast"
  # bash -c "python -m unittest tests.models.test_magenta.TestModelGeneration.test_isupper --failfast"