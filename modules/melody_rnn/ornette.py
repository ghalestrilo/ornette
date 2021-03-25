import magenta
from magenta import music as mm
from magenta.models.melody_rnn import melody_rnn_model
from magenta.models.melody_rnn.melody_rnn_sequence_generator import MelodyRnnSequenceGenerator
from magenta.models.shared import sequence_generator_bundle
from note_seq.protobuf import generator_pb2

class OrnetteModule():
  def constructor(self):
    self.model = MelodyRnnSequenceGenerator(
      model=melody_rnn_model.MelodyRnnModel(config),
      details=config.details,
      steps_per_quarter=steps_per_quarter,
      bundle=bundle_file)
    pass

  def generate(pitches, start_times, durations, tempo, length):
      qpm = tempo/2
      primer_sequence = make_notes_sequence(pitches, start_times, durations, qpm)

      generator_options = generator_pb2.GeneratorOptions()
      # Set the start time to begin on the next step after the last note ends.
      last_end_time = (max(n.end_time for n in primer_sequence.notes)
                      if primer_sequence.notes else 0)

      generator_options.generate_sections.add(
          start_time=last_end_time + _steps_to_seconds(1, qpm),
          end_time=length)

      # generate the output sequence
      generated_sequence = generator.generate(primer_sequence, generator_options)

      predicted_pitches = [note.pitch for note in generated_sequence.notes]
      predicted_start_times = [note.start_time for note in generated_sequence.notes]
      predicted_durations = [note.end_time - note.start_time for note in generated_sequence.notes]
      return {"pitches": predicted_pitches, "start_times": predicted_start_times, "durations": predicted_durations}