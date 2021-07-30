import magenta
from magenta.models.melody_rnn.melody_rnn_model import MelodyRnnModel, default_configs
from magenta.models.melody_rnn.melody_rnn_sequence_generator import MelodyRnnSequenceGenerator
from magenta.models.shared import sequence_generator_bundle
from note_seq.protobuf import generator_pb2

import os

class OrnetteModule():
    def __init__(self, host, checkpoint='attention_rnn'):
        self.config = default_configs[checkpoint]
        config = self.config
        checkpoint_file = os.path.normpath(f'/ckpt/{checkpoint}')
        bundle_file = sequence_generator_bundle.read_bundle_file(
            checkpoint_file)
        self.model = MelodyRnnSequenceGenerator(model=MelodyRnnModel(config),
                                                details=config.details,
                                                steps_per_quarter=config.steps_per_quarter,
                                                bundle=bundle_file)
        self.server_state = host.state
        self.host = host
        self.host.set('steps_per_quarter', config.steps_per_quarter)
        self.host.set('input_length', 16)
        self.host.set('input_unit', 'bars')
        self.host.set('output_unit', 'bars')
        self.last_end_time = 0
        self.host.set('last_end_time', 0)
        self.host.set('voices', [1])

        # TODO: Move to yaml
        self.host.include_filters('magenta')
        self.host.add_filter('input', 'midotrack2noteseq')
        self.host.add_filter('output', 'noteseq2midotrack')
        self.host.add_filter('output', 'mido_track_sort_by_time')
        self.host.add_filter('output', 'mido_track_subtract_last_time')

    def generate(self, tracks=None, length_seconds=4, voices=[0]):
        # output = []

        last_end_time = max([max([0, *(note.end_time for note in track.notes if any(track.notes))])
          for track
          in tracks])

        # self.config.steps_per_second = 100 * self.host.get('bpm') / 120
        generator_options = generator_pb2.GeneratorOptions()
        generator_options.generate_sections.add(
            start_time=last_end_time,
            end_time=last_end_time + length_seconds)

        generator_options.args['temperature'].float_value = 1.0
        generator_options.args['beam_size'].int_value = 1
        generator_options.args['branch_factor'].int_value = 1
        generator_options.args['steps_per_iteration'].int_value = 1
        generator_options.args['condition_on_primer'].bool_value = True
        generator_options.args['no_inject_primer_during_generation'].bool_value = True
        generator_options.args['inject_primer_during_generation'].bool_value = False

        output = [self.model.generate(tracks[voice], generator_options) for voice in voices]

        # for voice in voices:
        #   # Get last end time
        #   notes = 
        #   output.append(notes)
        # for seq in output:
        #   seq.notes = [n for n in seq.notes if n.start_time > last_end_time]

        return output

    def close(self):
        pass
      