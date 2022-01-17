# Ornette
### Let AI Make Music

**Ornette** an OSC-based command-line application to use ML models for continuous music generation.
You can control (manually or programatically) ML-based music generation and playback via text commands, OSC messaging or with command-line arguments. You can also try out different models through the same interface.

![Ornette Demo](./media/ornette-demo.gif)

The preview above shows **Ornette** running the [*PerformanceRNN*][url-performance-rnn] model in the left panel and sending data to the [**SuperCollider**][url-sc] instance to the right, which then generates sound (except when recorded as an SVG file)

## Concept

Ornette is an interactive container-based music generation Machine Learning model host and MIDI data workstation. Audio playback is completely delegated to external systems: at the moment, [**SuperCollider**][url-sc] using the [**SuperDirt**][url-sd] quark.

Ornette delegates audio synthesis to [**SuperCollider**][url-sc] and uses [**Docker**][url-docker] for environment management.

Ornette allows you to:
- Load MIDI files as prompts, 

## Requirements

- Python > 3.0
- [Pip][url-pip]
- [Docker][url-docker]
- [SuperCollider][url-sc]
  - [SuperDirt][url-sd] (a SuperCollider Quark)

## Running

1. Clone the repo (`git clone git://github.com/ghalestrilo/ornette.git`)
2. Run `pip install -e requirements.txt`
3. Run the host with `python .`. You'll be prompted to choose an RNN model and bundle
  - Optionally. pass `--modelname=<desired model> --checkpoint=<desired checkpoint>` to dismiss these prompts
5. To hear playback, make sure SuperCollider is running SuperDirt (either `sclang` or `scide` is fine)

### Example

Use the following command to start running MelodyRNN:

```bash
python . --model=melody_rnn --checkpoint=basic_rnn
```

Once started, you can issue commands to the serve, such as:

- `start` to begin playing
- `pause` to stop playing
- `reset` to clear current track
- `save <filename>` to save current track to a midi file on the `output` folder
- `generate 1 bars` to generate a single bar. "1" can be replaced by any positive integer


### Module Info

Modules are listed on the `modules` folder, and their bundles can be found on the `.ornette.yml` file. Most of the models were developed by [Magenta Research](https://github.com/magenta/magenta/tree/master/magenta/models). These are the currently implemented modules:


| modelname          | checkpoint                                    |
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


## Roadmap

  - [ ] Fix generation bugs with current models
  - [ ] Integrate new models
  - [ ] (maybe) Core engine rewrite in [Elixir][url-ex] with [ratatouille][url-rat] as a front-end framework
  - [ ] Improve UI
    - [ ] Improve and extend controls
    - [ ] Help tooltips
    - [ ] Improved error reporting
    - [ ] Model selection menu
  - [ ] Refactor and improve module API
    - [ ] Decouple modules from server using websockets for real-time data transfer
    - [ ] Extend `.ornette.yml` functionality
  - [ ] Send/receive MIDI Clock
  - [ ] Implement/use MIDI backend alternatives to SuperCollider/SuperDirt



[url-ex]:https://elixir-lang.org/
[url-rat]:https://hexdocs.pm/ratatouille/readme.html
[url-sc]:https://github.com/supercollider/supercollider
[url-pip]:https://pypi.org/project/pip/
[url-sd]:https://github.com/musikinformatik/SuperDirt
[url-docker]:https://www.docker.com/
[url-performance-rnn]:https://magenta.tensorflow.org/performance-rnn
