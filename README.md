# Ornette

An OSC-based command-line application to use ML models for music generation in real time.
You can control (manually or programatically) ML-based music generation and playback via text commands, OSC messaging or with command-line arguments. You can also try out different models through the same interface.

Ornette delegates audio synthesis to **SuperCollider** and uses **Docker** for environment management.

Ornette allows you to:
- Load MIDI files as prompts, 


⚠ This is **very** work-in-progress at the moment and will quite possibly break ⚠



## Concept

## Requirements

- Python > 3.0
- Pip
- [Docker](https://www.docker.com/)
- [SuperCollider](https://github.com/supercollider/supercollider)
  - [SuperDirt](https://github.com/musikinformatik/SuperDirt) (a SuperCollider Quark)


## Running

1. Clone the repo
2. Run `pip install -e requirements.txt`
3. Run the host with `python .`. You'll be prompted to choose an RNN model and bundle
  - Optionally. pass `--modelname=<desired model> --checkpoint=<desired checkpoint>` to dismiss these prompts
5. To hear playback, make sure SuperCollider is running SuperDirt (either `sclang` or `scide` is fine)

### Example

Use the following command to start serving MelodyRNN:

```bash
python . --checkpoint=melody_rnn --checkpoint=basic_rnn
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
- `/generate 1 bars` to generate a single bar. "1" can be replaced by any positive integer


### Full Guide

Currently, you can serve specific modules with the following syntax:

```bash
./start.sh <module_name> <checkpoint_name>
```

Modules are listed on the `modules` folder, and their bundles can be found on the `.ornette.yml` file. Most of the models were developed by [Magenta Research](https://github.com/magenta/magenta/tree/master/magenta/models). These are the currently implemented modules:


| model              | bundle                                        |
| ------------------ | --------------------------------------------- |
| melody_rnn         | basic_rnn                                     |
| melody_rnn         | mono_rnn                                      |
| melody_rnn         | lookback_rnn                                  |
| melody_rnn         | attention_rnn                                 |
| performance_rnn    | polyphony_rnn                                 |
| performance_rnn    | performance                                   |
| performance_rnn    | performance_with_dynamics                     |
| performance_rnn    | performance_with_dynamics_and_modulo_encoding |
| performance_rnn    | pitch_conditioned_performance_with_dynamics   |
| performance_rnn    | multiconditioned_performance_with_dynamics    |
| pianoroll_rnn_nade | rnn-nade_attn                                 |
| polyphony_rnn      | polyphony_rnn                                 |


## Future Work

- Receiving user input for interactive playback
- A friendlier terminal user interface in [nubia](https://github.com/facebookincubator/python-nubia) or [rich](https://github.com/willmcgugan/rich)
- Improved module configuration loading
- Other models
- MIDI Clock In/Out
- Support for other sound engines (?)
