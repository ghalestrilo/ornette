#!/bin/bash

declare -a models
declare -a checkpoints

models=(melody_rnn performance_rnn polyphony_rnn)
checkpoints=(attention_rnn performance_with_dynamics polyphony_rnn)

# models=(melody_rnn)
# checkpoints=(attention_rnn)

count=${#models[@]}

i=0
while (( $i < $count )); do
    eval "NOT_INTERACTIVE=1 ./start.sh ${models[$i]} ${checkpoints[$i]}" \
    & eval "NOT_INTERACTIVE=1 MODELNAME=${models[$i]} ./start.sh batch"

  i=($i+1)
done
