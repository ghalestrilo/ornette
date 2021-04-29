import math
import magenta
from magenta import music as mm
from note_seq.protobuf import generator_pb2
from note_seq import NoteSequence

from magenta.models.performance_rnn.performance_model import default_configs, PerformanceRnnModel
from magenta.models.performance_rnn.performance_sequence_generator import PerformanceRnnSequenceGenerator
from magenta.models.shared import sequence_generator
from magenta.models.shared import sequence_generator_bundle

import os


class OrnetteModule():
    def __init__(self, host, checkpoint='performance_with_dynamics'):
        config = default_configs[checkpoint]

        # TODO: improve checkpoint-loading logic
        bundle_path = os.path.normpath(f'/ckpt/{checkpoint}')
        bundle_file = sequence_generator_bundle.read_bundle_file(bundle_path)

        self.server_state = host.state
        self.host = host
        self.host.set('history', [[]])
        self.host.set('generation_unit', 'seconds')
        self.last_end_time = 0

        self.model = PerformanceRnnSequenceGenerator(
            model=PerformanceRnnModel(config),
            details=config.details,
            steps_per_second=config.steps_per_second,
            num_velocity_bins=config.num_velocity_bins,
            control_signals=config.control_signals,
            optional_conditioning=config.optional_conditioning,
            # checkpoint=os.path.normpath(f'/ckpt/{checkpoint}'),
            bundle=bundle_file,
            note_performance=config.note_performance)

    # update Module#generate to receive only number of tokens
    def generate(self, history=None, length_seconds=4):
        last_end_time = 0

        # Get first voice
        primer_sequence = [] if history is None else history[0]

        # Get last end time
        if (primer_sequence != None and any(primer_sequence)):
            last_end_time = max(n.end_time for n in primer_sequence)

        generator_options = generator_pb2.GeneratorOptions()
        generator_options.generate_sections.add(
            start_time=last_end_time,
            end_time=last_end_time + length_seconds)

        # TEMP: Constructing noteseq dict to feed into the model
        # TODO: bind 'notes' value to self.history
        noteseq = NoteSequence(
            notes=primer_sequence,
            quantization_info={
                'steps_per_quarter': self.server_state['steps_per_quarter']},
            tempos=[{'time': 0, 'qpm': self.server_state['bpm']}],
            total_quantized_steps=11,
        )

        seq = self.model.generate(noteseq, generator_options).notes
        def by_start_time(e): return e.start_time if e is not None else []
        seq.sort(key=by_start_time)
        return seq

    def decode(self, token):
        ''' Must return a mido message array (type (note_on), note, velocity, duration)'''
        velocity = 127

        start = max(0, token.start_time - self.last_end_time)
        end   = max(0, token.end_time - token.start_time)
        decoded = [
            ('note_on', token.pitch, token.velocity, start),
            ('note_off', token.pitch, token.velocity, end)
        ]

        self.last_end_time = max(0, token.end_time)
        return decoded

    def encode(self, message):
        ''' Receives a mido message, must return a model-compatible token '''

        next_start_time = self.last_end_time + message.time

        note = NoteSequence.Note(
            instrument=0,
            program=0,
            start_time=self.last_end_time,
            end_time=next_start_time,
            velocity=message.velocity,
            pitch=message.note,
        )

        self.last_end_time = next_start_time
        return note

    def close(self):
        pass
