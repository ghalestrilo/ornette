from note_seq import NoteSequence, PianorollSequence
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

def midotrack2pianoroll(tracks, host):
    init_pitch = host.get('init_pitch')
    primer_sequence = []
    step_length = 1 / host.get('steps_per_quarter')
    for i, own_note in enumerate(tracks[0]):
      partner_note = tracks[1][i]
      primer_sequence.append((own_note, partner_note) if partner_note else (own_note,))

    if not any(primer_sequence): primer_sequence = [(init_pitch,)]

    # Get last end time
    last_end_time = (len(primer_sequence) * step_length
      if primer_sequence != None and any(primer_sequence)
      else 0 )
    host.set('last_end_time', last_end_time)

    return PianorollSequence(
      events_list=primer_sequence,
      steps_per_quarter=host.get('steps_per_quarter'),
      shift_range=True)


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





def pianoroll2midotrack(pianoroll, host):
  output = []
  step_length = 1 / host.get('steps_per_quarter')
  for note_tuple in pianoroll.notes:
    while len(note_tuple) > len(output): output.append([])

    # Parse event and create message
    for i, note in enumerate(note_tuple):
      output[i].append(Message('note_on',
        note=note,
        channel=host.get('voices')[i],
        velocity=note.velocity,
        time=step_length
        ))

    # Pad eventless tracks
    for i in range(len(note_tuple) - len(output)): 
      if len(output[-i]):
        output[-i][-1].time += step_length
      else:
        output[-i].append(Message('note_off',
          note=0,
          channel=host.get('voices')[i],
          velocity=note.velocity,
          time=step_length
          ))
  return output





filters = {
  # Input
  'midotrack2noteseq': midotrack2noteseq,
  'midotrack2pianoroll': midotrack2pianoroll,

  # Output
  'noteseq2midotrack': noteseq2midotrack,
  'pianoroll2midotrack': pianoroll2midotrack,
}