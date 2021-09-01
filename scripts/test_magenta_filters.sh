#!/bin/bash
docker run -it -e "TERM=xterm-256color" -v $(pwd):/ornette ornette/melody_rnn  bash -c "python -m unittest tests/filters/test_magenta.py"