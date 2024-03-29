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

import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()
tf.autograph.set_verbosity(5, alsologtostdout=True)
from magenta.models.polyphony_rnn import polyphony_model
from magenta.models.polyphony_rnn import polyphony_sequence_generator
from magenta.models.shared import sequence_generator
from magenta.models.shared import sequence_generator_bundle
import note_seq
from note_seq.protobuf import generator_pb2
from note_seq.protobuf import music_pb2
from note_seq import NoteSequence



class OrnetteModule():
  def __init__(self, host, checkpoint='polyphony_rnn'):
      config          = polyphony_model.default_configs['polyphony']
      checkpoint_file = host.get_bundle(checkpoint)
      # checkpoint_file = os.path.normpath(f'/ckpt/{checkpoint}')
      bundle_file     = sequence_generator_bundle.read_bundle_file(checkpoint_file)
      self.model      = polyphony_sequence_generator.PolyphonyRnnSequenceGenerator(
        model=polyphony_model.PolyphonyRnnModel(config),
        details=config.details,
        steps_per_quarter=config.steps_per_quarter,
        bundle=bundle_file)
      self.server_state = host.state
      self.host = host
      self.host.set('output_unit', 'seconds')
      self.host.set('input_unit', 'seconds')
      self.host.set('input_length', 2)
      self.host.set('input_length', 2)
      self.generation_start = 0
      self.host.set('output_tracks', [1])
      self.host.set('steps_per_quarter', 4)
      self.host.set('trigger_generate', 0.1)

      # self.host.set('gen_offset', 1)
      
      
      # TODO: Move to yaml
      self.host.include_filters('magenta')
      self.host.add_filter('input', 'midotrack2noteseq')
      self.host.add_filter('input', 'merge_noteseqs')
      self.host.add_filter('input', 'debug_generation_request')
      self.host.add_filter('output', 'noteseq_trim_start')
      self.host.add_filter('output', 'noteseq_trim_end')
      self.host.add_filter('output', 'noteseq2midotrack')
      self.host.add_filter('output', 'mido_track_sort_by_time')
      self.host.add_filter('output', 'mido_track_subtract_previous_time')

  def generate(self, tracks=None, length_bars=4, output_tracks=[0]):
      output = []
      generation_start = self.host.get('generation_start')
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
        start_time=generation_start,
        end_time=generation_start + length_bars + buffer_length)

      output = [self.model.generate(tracks[index], generator_options) for index in [0]]
      return output

  def close(self):
      pass
