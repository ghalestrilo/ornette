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
      self.host.set('generation_unit', 'seconds')
      self.host.set('output_unit', 'beats')
      self.host.set('input_unit', 'beats')
      self.last_end_time = 0
      self.host.set('voices', [1])
      self.host.set('steps_per_quarter', 4)
      
      # TODO: Move to yaml
      self.host.add_filter('input', 'midotrack2noteseq')
      self.host.add_filter('output', 'noteseq2midotrack')

  def generate(self, tracks=None, length_seconds=4, voices=[0]):
      output = []

      last_end_time = max([max([0, *(note.end_time for note in track.notes if any(track.notes))]) for track in tracks])

      for voice in voices:
        # Get last end time

        generator_options = generator_pb2.GeneratorOptions()
        generator_options.generate_sections.add(
            start_time=last_end_time,
            end_time=last_end_time + length_seconds)

        notes = self.model.generate(tracks[voice], generator_options).notes
        output.append(notes)
      return output

  def close(self):
      pass