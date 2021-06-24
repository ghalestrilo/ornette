from note_seq import NoteSequence
from mido import MidiFile, Message

# Magenta Filters

## Input Filters
def midotrack2noteseq(tracks, host):
    seqs = []
    for track in tracks:
      seqs.append([])
      last_end_time = 0
      for message in track:
        next_start_time = last_end_time + host.song.from_ticks(message.time, host.get('input_unit'))
        if not message.is_meta:
          seqs[-1].append(NoteSequence.Note(
              instrument=0,
              program=0,
              start_time=last_end_time,
              end_time=next_start_time,
              velocity=message.velocity,
              pitch=message.note
              ))
        last_end_time = next_start_time

    return [NoteSequence(
        notes=seq,
        quantization_info={
            'steps_per_quarter': host.get('steps_per_quarter')},
        tempos=[{ 'time': 0, 'qpm': host.get('bpm') }],
        total_quantized_steps=11,
    ) for seq in seqs]

## Output Filters
def noteseq2midotrack(noteseqs, host):
    output = []

    # Convert Notes to Messages
    for i, notes in enumerate(noteseqs):
      output.append([])
      for (name, get_time) in [
            ('note_off', lambda x: x.end_time),
            ('note_on', lambda x: x.start_time)
          ]:
        for note in notes:
          ticks = host.song.to_ticks(get_time(note), host.get('output_unit'))
          ticks = int(round(ticks))

          output[-1].append(Message(name,
            note=note.pitch,
            channel=host.get('voices')[i],
            velocity=note.velocity,
            time=ticks
            ))

    # Sort by start_time
    output[-1].sort(key = lambda msg: msg.time)

    # Adjust note time
    last_time = 0
    for msg in output[-1]:
      dur = msg.time - last_time
      msg.time = dur
      last_time += dur
    return output

filters = {
  'midotrack2noteseq': midotrack2noteseq,
  'noteseq2midotrack': noteseq2midotrack,
}

class Filters():
  def __init__(self, host):
    self.host = host
    self._filters = filters.copy()
    host.filters = self
    self.input = []
    self.output = []

  def clear(self):
    self.input = []
    self.output = []

  def get(self, filtername):
    filter_ = None
    try:
      filter_ = self._filters[filtername]
    except KeyError:
      self.host.io.log(f'Ignoring unknown filter: {filtername}')

    return filter_

  def append(self, stage, filtername):
    f = self.get(filtername)
    if not f: return

    if stage == 'input': self.input.append(f)
    elif stage == 'output': self.output.append(f)
    else:
      self.host.io.log(f'Unknown filter stage: ({stage}), expected "input" or "output"')

  def set(self, input_filters, output_filters):
    self.clear()

    for filtername in input_filters: self.append('input', filtername)
    for filtername in output_filters: self.append('output', filtername)

