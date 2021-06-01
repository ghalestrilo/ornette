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
        self.host.set('generation_unit', 'seconds')
        self.host.set('last_end_time', 0)
        self.host.set('voices', [1])

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

    def generate(self, tracks=None, length_seconds=4, voices=[0]):
        output = []
        for voice in voices:
            # track = tracks[voice]

            # Get last end time
            # last_end_time = 0
            # if (tracks != None and any(tracks)):
            last_end_time = max([0, *(n.notes[0].end_time for n in tracks if any(n.notes))])

            generator_options = generator_pb2.GeneratorOptions()
            generator_options.generate_sections.add(
                start_time=last_end_time,
                end_time=last_end_time + length_seconds)

            print(tracks)
            seq = self.model.generate(tracks[voice], generator_options).notes
            # def by_start_time(e): return e.start_time if e is not None else []
            # seq.sort(key=by_start_time)
            output.append(seq)

        return output


    # TODO: Deprecate
    # def decode(self, token):
    #     ''' Must return a mido message array (type (note_on), note, velocity, duration)'''

    #     start = max(0, token.start_time - self.host.get('last_end_time'))
    #     end   = max(0, token.end_time - token.start_time)
    #     decoded = [
    #         ('note_on', token.pitch, token.velocity, start),
    #         ('note_off', token.pitch, token.velocity, end)
    #     ]

    #     self.host.set('last_end_time', max(0, token.end_time))
    #     return decoded


    # # TODO: Deprecate
    # def encode(self, message):
    #     ''' Receives a mido message, must return a model-compatible token '''
    #     last_end_time = self.host.get('last_end_time')
    #     next_start_time = last_end_time + self.host.from_ticks(message.time, 'beats')

    #     note = NoteSequence.Note(
    #         instrument=0,
    #         program=0,
    #         start_time=last_end_time,
    #         end_time=next_start_time,
    #         velocity=message.velocity or 1,
    #         pitch=message.note,
    #     )

    #     self.host.set('last_end_time', next_start_time)
    #     return note

    def close(self):
        pass
