# Ornette
An OSC server to interact with different music-generating ML models. This is **very** work-in-progress at the moment and will probably break.

## Concept

## Dependencies

- [Docker](https://www.docker.com/)
- [SuperCollider](https://github.com/supercollider/supercollider)
  - [SuperDirt](https://github.com/musikinformatik/SuperDirt) (a SuperCollider Quark)

## Running

1. Clone the repo
2. On the root folder, run: `chmod +x ./start.sh`
3. Follow the instructions below

### Example

Use the following command to start a server running MelodyRNN:

```bash
./start.sh melody_rnn basic_rnn
```

On a different terminal, run this command:

```bash
./start.sh client
```

Issue commands to the server through the client application. For instance:

- `/start` to begin playing
- `/pause` to stop playing
- `/reset` to clear current track
- `/save <filename>` to save current track to a midi file on the `output` folder

### Full Guide

Currently, you can serve specific modules with the following syntax:

```bash
./start.sh <module_name> <checkpoint_name>
```

Modules are listed on the `modules` folder, and their checkpoints can be found on the `.ornette.yml` file. Most of the models were developed by [Magenta Research](https://github.com/magenta/magenta/tree/master/magenta/models). These are the currently implemented modules, with their checkpoint options listed as subitems:

- melody_rnn
  - basic_rnn
  - mono_rnn
  - lookback_rnn
  - attention_rnn
- performance_rnn
  - polyphony_rnn
  - performance
  - performance_with_dynamics
  - performance_with_dynamics_and_modulo_encoding
  - density_conditioned_performance_with_dynamics
  - pitch_conditioned_performance_with_dynamics
  - multiconditioned_performance_with_dynamics
- pianoroll_rnn_nade
  - rnn-nade_attn
- polyphony_rnn
  - polyphony_rnn

## Future Work

- Receiving user input for interactive playback
- A friendlier terminal user interface in Python instead of... bash...
  - [nubia](https://github.com/facebookincubator/python-nubia)
  - [Docker SDK](https://docker-py.readthedocs.io/en/stable/)
- Improved module configuration loading
- Other models
- MIDI Clock In/Out
- Support for other sound engines (?)
