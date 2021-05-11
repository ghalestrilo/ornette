# Copyright 2021 The Magenta Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Lint as: python3
"""Generate pianoroll tracks from a trained RNN-NADE checkpoint.
Uses flags to define operation.
"""
import ast
import os
import time

from magenta.models.pianoroll_rnn_nade.pianoroll_rnn_nade_model import default_configs, PianorollRnnNadeModel
from magenta.models.pianoroll_rnn_nade.pianoroll_rnn_nade_sequence_generator import PianorollRnnNadeSequenceGenerator
from magenta.models.shared import sequence_generator
from magenta.models.shared import sequence_generator_bundle
import note_seq
from note_seq import NoteSequence
from note_seq.protobuf import generator_pb2
from note_seq.protobuf import music_pb2
import tensorflow.compat.v1 as tf

class OrnetteModule():
    def __init__(self, host, checkpoint='rnn-nade_attn'):
        tf.logging.set_verbosity('INFO')
        bundle_path = os.path.normpath(f'/ckpt/{checkpoint}')
        config = default_configs[checkpoint]
        bundle_file = sequence_generator_bundle.read_bundle_file(bundle_path)

        self.server_state = host.state
        self.host = host
        self.host.set('history', [[]])
        self.host.set('generation_unit', 'seconds')
        self.host.set('last_end_time', 0.125)

        self.model = PianorollRnnNadeSequenceGenerator(
          model=PianorollRnnNadeModel(config),
          details=config.details,
          steps_per_quarter=config.steps_per_quarter,
          bundle=bundle_file)

    def generate(self, history=None, length_seconds=4):
        init_pitch = 55

        # Get first voice
        primer_sequence = history[0] if history and any(history[0]) else [(init_pitch,)] 

        # Get last end time
        last_end_time = (len(primer_sequence) * (1/8) # TODO: steps_per_quarter
          if primer_sequence != None and any(primer_sequence)
          else 0 )

        # noteseq = NoteSequence(
        #     notes=primer_sequence,
        #     quantization_info={
        #         'steps_per_quarter': self.server_state['steps_per_quarter']},
        #     tempos=[{'time': 0, 'qpm': self.server_state['bpm']}],
        #     total_quantized_steps=11,
        # )
        primer_pianoroll = note_seq.PianorollSequence(
          events_list=history[0] if any(history[0]) else [(init_pitch,)],
          steps_per_quarter=4,
          shift_range=True)
        # primer_pianoroll = note_seq.PianoRoll()

        generator_options = generator_pb2.GeneratorOptions()
        generator_options.generate_sections.add(
            start_time=last_end_time,
            end_time=last_end_time + length_seconds)

        primer_sequence = primer_pianoroll.to_sequence(qpm=self.host.get('bpm'))
        seq = self.model.generate(primer_sequence, generator_options).notes
        # def by_start_time(e): return e.start_time if e is not None else []
        # seq.sort(key=by_start_time)
        return seq


    def decode(self, token):
        ''' Must return a mido message array (type (note_on), note, velocity, duration)'''

        start = max(0, token.start_time - self.host.get('last_end_time'))
        decoded = [
            ('note_on', token.pitch, token.velocity, start),
            ('note_off', token.pitch, token.velocity, start + 1/8) # TODO: steps_per_quarter
        ]

        self.host.set('last_end_time', max(0, token.end_time))
        return decoded

    def encode(self, message):
        ''' Receives a mido message, must return a model-compatible token '''
        last_end_time = self.host.get('last_end_time')

        note = (message.note,)

        self.host.set('last_end_time', last_end_time + 1/8) # TODO: steps_per_quarter
        return note

    def close(self):
      return None


















# def get_checkpoint():
#   """Get the training dir or checkpoint path to be used by the model."""
#   if FLAGS.run_dir and FLAGS.bundle_file and not FLAGS.save_generator_bundle:
#     raise sequence_generator.SequenceGeneratorError(
#         'Cannot specify both bundle_file and run_dir')
#   if FLAGS.run_dir:
#     train_dir = os.path.join(os.path.expanduser(FLAGS.run_dir), 'train')
#     return train_dir
#   else:
#     return None


# def get_bundle():
#   """Returns a generator_pb2.GeneratorBundle object based read from bundle_file.
#   Returns:
#     Either a generator_pb2.GeneratorBundle or None if the bundle_file flag is
#     not set or the save_generator_bundle flag is set.
#   """
#   if FLAGS.save_generator_bundle:
#     return None
#   if FLAGS.bundle_file is None:
#     return None
#   bundle_file = os.path.expanduser(FLAGS.bundle_file)
#   return sequence_generator_bundle.read_bundle_file(bundle_file)


# def run_with_flags(generator):
#   """Generates pianoroll tracks and saves them as MIDI files.
#   Uses the options specified by the flags defined in this module.
#   Args:
#     generator: The PianorollRnnNadeSequenceGenerator to use for generation.
#   """
#   if not FLAGS.output_dir:
#     tf.logging.fatal('--output_dir required')
#     return
#   output_dir = os.path.expanduser(FLAGS.output_dir)

#   primer_midi = None
#   if FLAGS.primer_midi:
#     primer_midi = os.path.expanduser(FLAGS.primer_midi)

#   if not tf.gfile.Exists(output_dir):
#     tf.gfile.MakeDirs(output_dir)

#   primer_sequence = None
#   qpm = FLAGS.qpm if FLAGS.qpm else 60
#   if FLAGS.primer_pitches:
#     primer_sequence = music_pb2.NoteSequence()
#     primer_sequence.tempos.add().qpm = qpm
#     primer_sequence.ticks_per_quarter = note_seq.STANDARD_PPQ
#     for pitch in ast.literal_eval(FLAGS.primer_pitches):
#       note = primer_sequence.notes.add()
#       note.start_time = 0
#       note.end_time = 60.0 / qpm
#       note.pitch = pitch
#       note.velocity = 100
#     primer_sequence.total_time = primer_sequence.notes[-1].end_time
#   elif FLAGS.primer_pianoroll:
#     primer_pianoroll = note_seq.PianorollSequence(
#         events_list=ast.literal_eval(FLAGS.primer_pianoroll),
#         steps_per_quarter=4,
#         shift_range=True)
#     primer_sequence = primer_pianoroll.to_sequence(qpm=qpm)
#   elif primer_midi:
#     primer_sequence = note_seq.midi_file_to_sequence_proto(primer_midi)
#     if primer_sequence.tempos and primer_sequence.tempos[0].qpm:
#       qpm = primer_sequence.tempos[0].qpm
#   else:
#     tf.logging.warning(
#         'No priming sequence specified. Defaulting to empty sequence.')
#     primer_sequence = music_pb2.NoteSequence()
#     primer_sequence.tempos.add().qpm = qpm
#     primer_sequence.ticks_per_quarter = note_seq.STANDARD_PPQ

#   # Derive the total number of seconds to generate.
#   seconds_per_step = 60.0 / qpm / generator.steps_per_quarter
#   generate_end_time = FLAGS.num_steps * seconds_per_step

#   # Specify start/stop time for generation based on starting generation at the
#   # end of the priming sequence and continuing until the sequence is num_steps
#   # long.
#   generator_options = generator_pb2.GeneratorOptions()
#   # Set the start time to begin when the last note ends.
#   generate_section = generator_options.generate_sections.add(
#       start_time=primer_sequence.total_time,
#       end_time=generate_end_time)

#   if generate_section.start_time >= generate_section.end_time:
#     tf.logging.fatal(
#         'Priming sequence is longer than the total number of steps '
#         'requested: Priming sequence length: %s, Total length '
#         'requested: %s',
#         generate_section.start_time, generate_end_time)
#     return

#   generator_options.args['beam_size'].int_value = FLAGS.beam_size
#   generator_options.args['branch_factor'].int_value = FLAGS.branch_factor

#   tf.logging.info('primer_sequence: %s', primer_sequence)
#   tf.logging.info('generator_options: %s', generator_options)

#   # Make the generate request num_outputs times and save the output as midi
#   # files.
#   date_and_time = time.strftime('%Y-%m-%d_%H%M%S')
#   digits = len(str(FLAGS.num_outputs))
#   for i in range(FLAGS.num_outputs):
#     generated_sequence = generator.generate(primer_sequence, generator_options)

#     midi_filename = '%s_%s.mid' % (date_and_time, str(i + 1).zfill(digits))
#     midi_path = os.path.join(output_dir, midi_filename)
#     note_seq.sequence_proto_to_midi_file(generated_sequence, midi_path)

#   tf.logging.info('Wrote %d MIDI files to %s',
#                   FLAGS.num_outputs, output_dir)


# def main(unused_argv):
#   """Saves bundle or runs generator based on flags."""
#   tf.logging.set_verbosity(FLAGS.log)

#   bundle = get_bundle()

#   config_id = bundle.generator_details.id if bundle else FLAGS.config
#   config = pianoroll_rnn_nade_model.default_configs[config_id]
#   config.hparams.parse(FLAGS.hparams)
#   # Having too large of a batch size will slow generation down unnecessarily.
#   config.hparams.batch_size = min(
#       config.hparams.batch_size, FLAGS.beam_size * FLAGS.branch_factor)

#   generator = PianorollRnnNadeSequenceGenerator(
#       model=pianoroll_rnn_nade_model.PianorollRnnNadeModel(config),
#       details=config.details,
#       steps_per_quarter=config.steps_per_quarter,
#       checkpoint=get_checkpoint(),
#       bundle=bundle)

#   if FLAGS.save_generator_bundle:
#     bundle_filename = os.path.expanduser(FLAGS.bundle_file)
#     if FLAGS.bundle_description is None:
#       tf.logging.warning('No bundle description provided.')
#     tf.logging.info('Saving generator bundle to %s', bundle_filename)
#     generator.create_bundle_file(bundle_filename, FLAGS.bundle_description)
#   else:
#     run_with_flags(generator)

