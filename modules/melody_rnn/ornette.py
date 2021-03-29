import magenta
from magenta import music as mm
from magenta.models.melody_rnn import melody_rnn_model
from magenta.models.melody_rnn.melody_rnn_sequence_generator import MelodyRnnSequenceGenerator
from magenta.models.shared import sequence_generator_bundle
from note_seq.protobuf import generator_pb2
from note_seq import NoteSequence

# TODO: not cross-platform
MODEL_DIR='/model'
CHECKPOINT_DIR='/model/checkpoint'

# TODO: Use in server
def _steps_to_seconds(steps, qpm):
    steps_per_quarter = 4
    return steps * 60.0 / qpm / steps_per_quarter






















## FIXME: Deprecate!!
def make_midi(pitches, start_times, durations, qpm, midi_path):
    track    = 0
    channel  = 0
    time     = 0
    volume   = 100
    MyMIDI = MIDIFile(1)
    MyMIDI.addTempo(track, time, qpm)

    for pitch, start_time, duration in zip(pitches,start_times,durations):
        MyMIDI.addNote(track, channel, pitch, start_time, duration, volume)
        print(MyMIDI)

    with open(midi_path, "wb") as output_file:
        MyMIDI.writeFile(output_file)

def make_notes_sequence(pitches, start_times, durations, qpm):
    TEMP_MIDI = "temp.mid"
    make_midi(pitches, start_times, durations, qpm, TEMP_MIDI)
    return mm.midi_file_to_sequence_proto(TEMP_MIDI)
## FIXME: Deprecate!!













import os



class OrnetteModule():
  def __init__(self, state={}, checkpoint='attention_rnn'):
    config      = magenta.models.melody_rnn.melody_rnn_model.default_configs[checkpoint]
    checkpoint_file = os.path.normpath(f'/ckpt/{checkpoint}')
    bundle_file = sequence_generator_bundle.read_bundle_file(checkpoint_file)
    steps_per_quarter = 4
    self.model = MelodyRnnSequenceGenerator(model=melody_rnn_model.MelodyRnnModel(config),
      details=config.details,
      steps_per_quarter=steps_per_quarter,
      bundle=bundle_file)
    self.realtime_ready = True
    # self.temperature=1.2
    self.server_state = state
    # self.server_state['history'] = [None] # FIXME: How to properly do this?
    self.server_state['history'] = [[]]

  def generate(self, primer_sequence=None):
      qpm = self.server_state['tempo']/2

      # length = self.server_state['max_buffer'];
      length = 16
      
      #primer_sequence = make_notes_sequence(pitches, start_times, durations, qpm)

      
      # Set the start time to begin on the next step after the last note ends.
      last_end_time = 0
      
      if (len(self.server_state['history'][0]) > 0 and primer_sequence != None):
          last_end_time = max(n.end_time for n in primer_sequence.notes) if primer_sequence.notes else 0

      # TODO: Move to constructor
      generator_options = generator_pb2.GeneratorOptions()
      generator_options.generate_sections.add(
          start_time=last_end_time + _steps_to_seconds(1, qpm),
          end_time=length)

      # TEMP: Constructing noteseq dict to feed into the model
      # TODO: bind 'notes' value to self.history
      noteseq = {
          'notes': primer_sequence,
          'quantizationInfo': {
            'stepsPerQuarter': 4
            },
          'tempos': [ { 'time': 0, 'qpm': 120}],
          'totalQuantizedSteps': 11,
      }

      noteseq = NoteSequence(
        notes=primer_sequence,
        quantization_info={
            'steps_per_quarter': 4
            },
        tempos=[ { 'time': 0, 'qpm': 120}],
        total_quantized_steps=11,
      )

      # generate the output sequence
      generated_sequence = self.model.generate(noteseq, generator_options)

      # predicted_pitches = [note.pitch for note in generated_sequence.notes]
      # predicted_start_times = [note.start_time for note in generated_sequence.notes]
      # predicted_durations = [note.end_time - note.start_time for note in generated_sequence.notes]
      # return {"pitches": predicted_pitches, "start_times": predicted_start_times, "durations": predicted_durations}
      return generated_sequence

  def tick(self, topk=1):
    return self.generate(self.server_state['history'][0]).notes
  
  def decode(self, token):
    pass

  def close(self):
    pass
  
  def update_feed_dict(self):
    pass