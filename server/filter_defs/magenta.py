from note_seq import NoteSequence, PianorollSequence
from note_seq.midi_io import note_sequence_to_pretty_midi
from magenta.music.sequences_lib import is_relative_quantized_sequence
from mido import MidiFile, Message

# Magenta Filters

## Input Filters
def midotrack2noteseq(tracks, host):
    seqs = []
    velocity_sensitive = host.get('is_velocity_sensitive')
    for track in tracks:
      seqs.append([])
      last_end_time = 0
      for message in track:
        
        # AttributeError:
        # 'str' object has no attribute 'time'
        if isinstance(message, str): continue

        next_start_time = last_end_time + host.song.from_ticks(message.time, host.get('input_unit'))
        if not message.is_meta:
          note = NoteSequence.Note(
              instrument=0,
              program=0,
              start_time=last_end_time,
              end_time=next_start_time,
              velocity=message.velocity,
              pitch=message.note
              )
          if velocity_sensitive and message.velocity:
            note.velocity = message.velocity
          seqs[-1].append(note)
        last_end_time = next_start_time

    # Calculate total quantized steps
    # total_quantized_steps = max(seq[0].end_time for seq in seqs) - min(seq[0].start_time for seq in seqs)
    # total_quantized_steps = host.song.convert(total_quantized_steps, 'beats', 'steps')

    return [NoteSequence(
        notes=seq,
        quantization_info={
            'steps_per_quarter': host.get('steps_per_quarter')},
        tempos=[{ 'time': 0, 'qpm': host.get('bpm') }],
        # total_quantized_steps = total_quantized_steps,
        # total_quantized_steps = 
    ) for seq in seqs]

def midotrack2pianoroll(tracks, host):
    init_pitch = host.get('init_pitch')
    primer_sequence = []
    step_length = 1 / host.get('steps_per_quarter')
    
    # Create empty PianorollSequence
    noteseq = NoteSequence(
      quantization_info={'steps_per_quarter': host.get('steps_per_quarter')},
      tempos=[{ 'time': 0, 'qpm': host.get('bpm') }],
    )
    pianorollseq = PianorollSequence(quantized_sequence=noteseq)
    # print(f'noteseq.quantization_info.steps_per_quarter: {noteseq.quantization_info.steps_per_quarter}')
    # print(f'relative quantized? {is_relative_quantized_sequence(noteseq)}')
    # print(tracks)
    
    for i, own_note in enumerate(tracks[0]):
      # print(own_note)
      if own_note.is_meta: continue # FIXME: This is bullshit, the song#buffer method should take care of this
      partner_note = tracks[1][i]
      own_note = own_note.note
      tuple_ = (own_note, partner_note) if partner_note else (own_note,)
      primer_sequence.append(tuple_)
      pianorollseq.append(tuple_)

    if not any(primer_sequence):
      primer_sequence = [(init_pitch,)]
      pianorollseq.append((init_pitch,))

    # Get last end time
    last_end_time = (len(primer_sequence) * step_length
      if primer_sequence != None and any(primer_sequence)
      else 0)
    host.set('last_end_time', last_end_time)

    return pianorollseq

## Output Filters
def noteseq2midotrack(noteseqs, host):
    output = []
    velocity_sensitive = host.get('is_velocity_sensitive')

    # Convert Notes to Messages
    for i, notes in enumerate(noteseqs):
      output.append([])
      for (name, get_time) in [
            ('note_off', lambda x: x.end_time),
            ('note_on', lambda x: x.start_time)
          ]:
        for note in notes:
          ticks = host.song.to_ticks(get_time(note), host.get('output_unit'))
          # ticks *= host.get('time_coeff')
          ticks = int(round(ticks))

          output[-1].append(Message(name,
            note=note.pitch,
            channel=host.get('voices')[i],
            velocity=note.velocity if velocity_sensitive else 100,
            time=ticks
            ))

    return output



def mido_track_sort_by_time(tracks, host):
  """ Sorts Track messages by time """
  for track in tracks:
    track.sort(key = lambda msg: msg.time)

  return tracks

def mido_track_subtract_last_time(tracks, host):
  """ Some models save accumulated time instead of note length """
  # Adjust note time
  for track in tracks:
    last_time = track[0].time if len(track) else 0
    for msg in track:
      dur = msg.time - last_time
      msg.time = dur
      last_time += dur
  
  return tracks

def noteseq2pianoroll(noteseq,host):
  return PianorollSequence(quantized_sequence=noteseq)

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























## Output Filters
def noteseq2midotrack_performance_rnn(noteseqs, host):
    output = []
    velocity_sensitive = host.get('is_velocity_sensitive')

    # Convert Notes to Messages
    print(noteseqs)
    for i, notes in enumerate(noteseqs):
      track = []
      for (name, get_time) in [
            ('note_off', lambda x: x.end_time),
            ('note_on', lambda x: x.start_time)
          ]:
        for note in notes:
          print(note)
          time = get_time(note) * 1000
          ticks = host.song.to_ticks(time, host.get('output_unit'))
          ticks = int(round(ticks / 1000))

          track.append(Message(name,
            note=note.pitch,
            channel=host.get('voices')[i],
            velocity=note.velocity if velocity_sensitive else 100,
            time=ticks
            ))

      # print('\n\n============')
      # for n in notes: print(f'pitch={n.pitch} start={n.start_time} end={n.end_time}')
      # print('============\n\n')

      # print('\n\n============')
      # for t in track: print(t)
      # print('============\n\n')

      if not any(track): continue
      
      # Calculate relative time
      timediff = [track[0].time] + [msg.time for msg in track]
      for i, message in enumerate(track):
        message.time -= timediff[i]

        # FIXME: Returned/Generated messages are too short
        # message.time *= 2


      output.append(track.copy())

    print(output)
    return output


# TODO: This is test code, move to a test case
def filter_test(noteseq_, host):
  noteseq = [ [63, 100, 3.81, 4.0]
            , [60, 100, 3.82, 4.0]
            , [54, 100, 3.83, 4.0]
            , [44, 100, 3.84, 4.0]
            ]

  noteseq = [NoteSequence.Note(
                instrument=0,
                program=0,
                start_time=start_time,
                end_time=end_time,
                velocity=velocity,
                pitch=pitch
                )
    for [pitch, velocity, start_time, end_time]
    in noteseq]
  noteseq = NoteSequence(
        notes=noteseq,
        quantization_info={
            'steps_per_quarter': host.get('steps_per_quarter')},
        tempos=[{ 'time': 0, 'qpm': host.get('bpm') }],
        ).notes
  # print(noteseq)

  midotrack = noteseq2midotrack_performance_rnn([noteseq], host)
  midotrack = midotrack[0]
  expected = [ Message('note_on', channel=1, note=63, velocity=100, time=0)
             , Message('note_on', channel=1, note=60, velocity=100, time=0.01)
             , Message('note_on', channel=1, note=54, velocity=100, time=0.01)
             , Message('note_on', channel=1, note=44, velocity=100, time=0.01)
             , Message('note_off', channel=1, note=63, velocity=100, time=0.16)
             , Message('note_off', channel=1, note=60, velocity=100, time=0)
             , Message('note_off', channel=1, note=54, velocity=100, time=0)
             , Message('note_off', channel=1, note=44, velocity=100, time=0)
             ]
  for msg in expected:
    msg.time = host.song.to_ticks(msg.time, host.get('output_unit'))

  print("\n\n===============")
  print(noteseq)
  for i in range(len(expected)):
    if len(midotrack) < i:
      print('These notes are missing:')
      print(expected[i:])
      break
    print(f'{expected[i]} \t| {midotrack[i]}')
  print("===============\n\n")
  exit()
  return noteseq_




def mido_no_0_velocity(tracks, host):
    """ 0-velocity messages crash PerformanceRNN
        This filter substitutes 0 velocity by 1
    """
    for track in tracks:
      for msg in track:
        if msg.type in ['note_on', 'note_off'] and msg.velocity == 0:
          msg.velocity = 1
    return tracks


filters = {
  # Input (Mido)
  'midotrack2noteseq': midotrack2noteseq,
  'midotrack2pianoroll': midotrack2pianoroll,
  'mido_no_0_velocity': mido_no_0_velocity,
  'filter_test': filter_test,

  # Output
  'noteseq2midotrack': noteseq2midotrack,
  'noteseq2midotrack_performance_rnn': noteseq2midotrack_performance_rnn,
  'noteseq2pianoroll': noteseq2pianoroll,
  'pianoroll2midotrack': pianoroll2midotrack,
  'mido_track_sort_by_time': mido_track_sort_by_time,
  'mido_track_subtract_last_time': mido_track_subtract_last_time,
}


