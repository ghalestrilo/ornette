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
"""Generate polyphonic tracks from a trained checkpoint.
Uses flags to define operation.
"""
import os

from magenta.models.polyphony_rnn import polyphony_model
from magenta.models.polyphony_rnn import polyphony_sequence_generator
from magenta.models.shared import sequence_generator
from magenta.models.shared import sequence_generator_bundle
import note_seq
from note_seq.protobuf import generator_pb2
from note_seq.protobuf import music_pb2
import tensorflow.compat.v1 as tf
from note_seq import NoteSequence

tf.disable_v2_behavior()

class OrnetteModule():
  def __init__(self, host, checkpoint='polyphony_rnn'):
      config          = polyphony_model.default_configs['polyphony']
      checkpoint_file = os.path.normpath(f'/ckpt/{checkpoint}')
      bundle_file     = sequence_generator_bundle.read_bundle_file(checkpoint_file)
      self.model      = polyphony_sequence_generator.PolyphonyRnnSequenceGenerator(
        model=polyphony_model.PolyphonyRnnModel(config),
        details=config.details,
        steps_per_quarter=config.steps_per_quarter,
        bundle=bundle_file)
      self.server_state = host.state
      self.host = host
      self.host.set('output_unit', 'measures')
      self.host.set('input_unit', 'measures')
      self.last_end_time = 0
      self.host.set('output_tracks', [1])
      self.host.set('steps_per_quarter', 4)
      self.host.set('trigger_generate', 0.1)
      
      # TODO: Move to yaml
      self.host.include_filters('magenta')
      self.host.add_filter('input', 'midotrack2noteseq')
      # self.host.add_filter('input', 'print_noteseqs')
      self.host.add_filter('input', 'merge_noteseqs')
      self.host.add_filter('output', 'print_noteseqs')
      self.host.add_filter('output', 'drop_input_length')
      self.host.add_filter('output', 'noteseq2midotrack')
      self.host.add_filter('output', 'mido_track_sort_by_time')
      self.host.add_filter('output', 'mido_track_subtract_last_time')

  def generate(self, tracks=None, length_bars=4, output_tracks=[0]):
      output = []
      # last_end_time = max([max([0, *(note.end_time for note in track.notes if any(track.notes))]) for track in tracks])
      last_end_time = max([0] + [note.end_time if any(track.notes) else 0
        for track in tracks
        for note in track.notes
        ])
      print(f'last_end_time: {last_end_time}')
      self.host.set('last_end_time', last_end_time)
      # buffer_length = last_end_time
      buffer_length = self.host.song.get_buffer_length()

      generator_options = generator_pb2.GeneratorOptions()

      generator_options.args['temperature'].float_value = 1.0
      generator_options.args['beam_size'].int_value = 1
      generator_options.args['branch_factor'].int_value = 1
      generator_options.args['steps_per_iteration'].int_value = 1
      generator_options.args['condition_on_primer'].bool_value = True
      generator_options.args['no_inject_primer_during_generation'].bool_value = False
      generator_options.args['inject_primer_during_generation'].bool_value = True

      generator_options.generate_sections.add(
        start_time=last_end_time,
        end_time=last_end_time + length_bars + buffer_length)

      output = [self.model.generate(tracks[index], generator_options) for index in output_tracks]
      return output

  def close(self):
      pass
