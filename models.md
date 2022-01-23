# Modelos que serão testados

- Modelos do Magenta:
    - Performance RNN: Representa codificação em Evento e arquitertura RNN-LSTM, configuração simples (disponível na lib magenta)
    - Improv RNN: Chord-based conditioning, Grid notation
    - Pianoroll RNN-NADE
    - Polyphony RNN
- REMI: Representa codificação em Grid e arquitetura Transformer. Para o próprio domínio (música Pop), apresenta resultados superiores ao Transformer Baseline
- MusicTransformer: Representa codificação em Eventos. Estado da arte em geração expressiva
- MusicVAE: Único modelo que expõe espaço latente
- BachDuet (RL-Duet): Modelo mais sofisticado de condicionamento.

## Performance RNN

* [performance](http://download.magenta.tensorflow.org/models/performance.mag)
* [performance_with_dynamics](http://download.magenta.tensorflow.org/models/performance_with_dynamics.mag)
* [performance_with_dynamics_and_modulo_encoding](http://download.magenta.tensorflow.org/models/performance_with_dynamics_and_modulo_encoding.mag)
* [density_conditioned_performance_with_dynamics](http://download.magenta.tensorflow.org/models/density_conditioned_performance_with_dynamics.mag)
* [pitch_conditioned_performance_with_dynamics](http://download.magenta.tensorflow.org/models/pitch_conditioned_performance_with_dynamics.mag)
* [multiconditioned_performance_with_dynamics](http://download.magenta.tensorflow.org/models/multiconditioned_performance_with_dynamics.mag)


## Improv RNN

```sh
BUNDLE_PATH=<absolute path of .mag file>
CONFIG=<one of 'basic_improv', 'attention_improv' or 'chord_pitches_improv', matching the bundle>

improv_rnn_generate \
  --config=${CONFIG} \
  --bundle_file=${BUNDLE_PATH} \
  --output_dir=/tmp/improv_rnn/generated \
  --num_outputs=10 \
  --primer_melody="[60]" \
  --backing_chords="C G Am F C G Am F" \
  --render_chords
```

## Pianoroll RNN-NADE

http://download.magenta.tensorflow.org/models/pianoroll_rnn_nade.mag
http://download.magenta.tensorflow.org/models/pianoroll_rnn_nade-bach.mag

```sh
BUNDLE_PATH=<absolute path of .mag file>

pianoroll_rnn_nade_generate \
  --bundle_file=${BUNDLE_PATH} \
  --output_dir=/tmp/pianoroll_rnn_nade/generated \
  --num_outputs=10 \
  --num_steps=128 \
  --primer_pitches="[67,64,60]"
```

## Polyphony RNN

checkpoint: http://download.magenta.tensorflow.org/models/polyphony_rnn.mag

BUNDLE_PATH=<absolute path of .mag file>

```
START
NEW_NOTE, 67
NEW_NOTE, 64
NEW_NOTE, 60
STEP_END
CONTINUED_NOTE, 67
CONTINUED_NOTE, 64
CONTINUED_NOTE, 60
STEP_END
CONTINUED_NOTE, 67
CONTINUED_NOTE, 64
CONTINUED_NOTE, 60
STEP_END
CONTINUED_NOTE, 67
CONTINUED_NOTE, 64
CONTINUED_NOTE, 60
STEP_END
END
```

```sh
polyphony_rnn_generate \
  --bundle_file=${BUNDLE_PATH} \
  --output_dir=/tmp/polyphony_rnn/generated \
  --num_outputs=10 \
  --num_steps=64 \
  --primer_melody="[60, -2, -2, -2, 60, -2, -2, -2, "\
  "67, -2, -2, -2, 67, -2, -2, -2, 69, -2, -2, -2, "\
  "69, -2, -2, -2, 67, -2, -2, -2, -2, -2, -2, -2]" \
  --condition_on_primer=false \
  --inject_primer_during_generation=true  
```