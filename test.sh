docker run \
  -v $HOME/.ornette/checkpoints:/checkpoints \
  -v $HOME/git/tg-server/output:/output \
  -v $HOME/git/tg-server:/ornette \
  -it ornette/pianoroll_rnn_nade \
  python -m unittest tests/test_filters.py