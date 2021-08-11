import os

MAGENTA_PATH=os.path.join(os.path.expanduser('~'), 'git', 'magenta')
if 'MAGENTA_PATH' in os.environ.keys(): MAGENTA_PATH = os.environ['MAGENTA_PATH']

ORNETTE_PATH=os.path.join(os.path.expanduser('~'), 'git', 'tg-server')
if 'ORNETTE_PATH' in os.environ.keys(): ORNETTE_PATH = os.environ['ORNETTE_PATH']

barcount = 16
# melody_rnn: steps = 256 (barcount * 4 * 4)
# perormance_rnn: steps = barcount * 2 * 100

number_of_samples = 10

# MelodyRNN: Generate samples
# docker run
# -v $HOME/.ornette/checkpoints:/checkpoints
# -v $HOME/git/ornette/output:/output
# -it ornette/melody_rnn bash

docker run \
  -v $HOME/.ornette/checkpoints:/checkpoints \
  -v $HOME/git/ornette/output:/output \
  -it ornette/melody_rnn \
  melody_rnn_generate \
    --config=attention_rnn \
    --bundle_file=/checkpoints/melody_rnn/attention_rnn \
    --output_dir=/output/melody_rnn \
    --num_outputs=$number_of_samples \
    --num_steps=256 \
    --primer_melody="[]"

# PerformanceRNN: Generate samples

docker run
  -v $HOME/.ornette/checkpoints:/checkpoints
  -v $HOME/git/ornette/output:/output
  -it ornette/performance_rnn \ 
  performance_rnn_generate \
    --config=performance_with_dynamics \
    --bundle_file=/checkpoints/performance_rnn/performance_with_dynamics \
    --output_dir=/output/baseline/performance_rnn \
    --num_outputs=$number_of_samples \
    --num_steps=3200 \
    --primer_melody="[]"
 

###############################################################################################

# TODO: Crop dataset (via ornette) samples before feeding to models

# Problem: Not monophonic melodies
docker run \
  -v $HOME/.ornette/checkpoints:/checkpoints \
  -v $HOME/git/tg-server/output:/output \
  -it ornette/melody_rnn \
  performance_rnn_generate \
    --config=attention_rnn \
    --bundle_file=/checkpoints/melody_rnn/attention_rnn \
    --output_dir=/output/baseline/melody_rnn \
    --num_outputs=$number_of_samples \
    --num_steps=256 \
    --primer_midi=/output/dataset/sample-0.mid

# OK
docker run \
  -v $HOME/.ornette/checkpoints:/checkpoints \
  -v $HOME/git/tg-server/output:/output \
  -it ornette/polyphony_rnn \
  polyphony_rnn_generate \
    --bundle_file=/checkpoints/polyphony_rnn/polyphony_rnn \
    --output_dir=/output/baseline/polyphony_rnn \
    --num_outputs=10 \
    --num_steps=256 \
    --primer_midi=/output/dataset/sample-0.mid \
    --condition_on_primer=true \
    --inject_primer_during_generation=false

# OK
docker run \
  -v $HOME/.ornette/checkpoints:/checkpoints \
  -v $HOME/git/tg-server/output:/output \
  -it ornette/pianoroll_rnn_nade \
  pianoroll_rnn_nade_generate \
    --config=rnn-nade_attn \
    --bundle_file=/checkpoints/pianoroll_rnn_nade/rnn-nade_attn \
    --output_dir=/output/baseline/pianoroll_rnn_nade \
    --num_outputs=4 \
    --num_steps=256 \
    --primer_midi=/output/dataset/sample-0.mid \

# OK
docker run \
  -v $HOME/.ornette/checkpoints:/checkpoints \
  -v $HOME/git/tg-server/output:/output \
  -it ornette/performance_rnn \
  performance_rnn_generate \
    --config=performance_with_dynamics \
    --bundle_file=/checkpoints/performance_rnn/performance_with_dynamics \
    --output_dir=/output/baseline/performance_rnn \
    --num_outputs=10 \
    --num_steps=6400 \
    --primer_midi=/output/dataset/sample-0.mid


# PerformanceRNN: testar multiplicar quantidade de steps (total quantized steps + time de cada beat) por 100