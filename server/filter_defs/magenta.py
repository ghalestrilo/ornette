from note_seq import NoteSequence, PianorollSequence
from note_seq.midi_io import note_sequence_to_pretty_midi
from magenta.music.sequences_lib import is_relative_quantized_sequence, quantize_note_sequence
from mido import MidiFile, Message
from itertools import takewhile

# Magenta Filters

def print_noteseqs(noteseqs, host, label=""):
  """ Prints a NoteSeq and returns it """
  print(f'[{label}] printing sequences')
  for i, noteseq in enumerate(noteseqs):
    print(f'\n sequence {i}')
    for note in noteseq.notes:
      print(f'pitch: {note.pitch}\t| velocity: {note.velocity}\t| start_time: {note.start_time:.4f}\t| end_time: {note.end_time:.4f}')
  return noteseqs

def drop_input_length(noteseqs, host):
  seq_start_time = host.song.get_buffer_length()

  print(f'dropping notes before: {seq_start_time}')
  for noteseq in noteseqs:
    if not any(noteseq.notes): continue
    while any(noteseq.notes) and noteseq.notes[0].start_time < seq_start_time:
      noteseq.notes.remove(noteseq.notes[0])
    for note in noteseq.notes:
      note.start_time -= seq_start_time
      note.end_time -= seq_start_time
  return noteseqs

## Input Filters
def midotrack2noteseq(tracks, host):
    """ Converts a list of Mido Tracks to a list of NoteSequences
        State: Tested, converts neatly
    """
    seqs = []
    qpm = 120 # IMPORTANT: The input qpm must be fixed to 120, otherwise the models will generate output in a wrong scale of times
    velocity_sensitive = host.get('is_velocity_sensitive')
    steps_per_quarter = host.get('steps_per_quarter')

    input_unit = host.get('input_unit')

    # tracks = [[msg in track for msg in track if not isinstance(msg, str) ] for track in tracks]

    for track in tracks:
      seqs.append([])
      # First create start_times, then end_times

      # seq_start_time = list(filter(lambda msg: msg.type == 'note_on', track))[:1]
      seq_start_time = next(filter(lambda msg: msg.type == 'note_on', track), None)
      seq_start_time = seq_start_time.time if seq_start_time else 0

      note_start_ticks = 0

      # enumerate track
      for (i, message) in enumerate(track):
        
        # AttributeError:
        # 'str' object has no attribute 'time'
        if isinstance(message, str): continue

        # Update note start time
        note_start_ticks += message.time

        # Calculate note duration
        rest = track[i:]
        rest = filter(lambda msg: not msg.is_meta, rest)
        ringing_interval = takewhile(lambda msg: msg.type != 'note_off' and msg.note != msg.note, rest)
        # print(list(ringing_interval))
        ringing_interval = map(lambda msg: msg.time, ringing_interval)
        duration = sum(ringing_interval)

        # Create Notes
        if not message.is_meta:
          note = NoteSequence.Note(
              instrument=0,
              program=0,
              start_time=host.song.from_ticks(note_start_ticks - seq_start_time, input_unit),
              end_time=host.song.from_ticks(note_start_ticks - seq_start_time + duration, input_unit),
              velocity=message.velocity,
              pitch=message.note
              )
          if velocity_sensitive and message.velocity:
            note.velocity = message.velocity
          seqs[-1].append(note)


    # Calculate Input Buffer Size
    total_quantized_steps = host.get('input_length')
    total_quantized_steps = host.song.convert(total_quantized_steps, host.get('input_unit'), 'beats')
    total_quantized_steps = int(round(total_quantized_steps))
    print(f'total_quantized_steps: {total_quantized_steps}')

    sequences = [NoteSequence(
        notes=seq.copy(),
        quantization_info={
          'steps_per_quarter': steps_per_quarter,
        },
        tempos=[{ 'time': 0, 'qpm': qpm }],
        total_quantized_steps=total_quantized_steps
    ) for seq in seqs]
    
    return sequences






def midotrack2pianoroll(tracks, host):
    init_pitch = host.get('init_pitch')
    primer_sequence = []
    step_length = 1 / host.get('steps_per_quarter')

    qpm = 120 # IMPORTANT: The input qpm must be fixed to 120, otherwise the models will generate output in a wrong scale of times

    # Create empty PianorollSequence
    noteseq = NoteSequence(
      quantization_info={ 'steps_per_quarter': host.get('steps_per_quarter') },
      tempos=[{ 'time': 0, 'qpm': qpm }], 
    )
    pianorollseq = PianorollSequence(quantized_sequence=noteseq)
    for i, own_note in enumerate(tracks[0]):
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
    noteseqs = [seq.notes for seq in noteseqs]

    buffer_size = host.get('last_end_time')

    # Convert Notes to Messages
    for (i, notes) in enumerate(noteseqs):
      output.append([])
      for (name, get_time) in [
            ('note_off', lambda x: x.end_time),
            ('note_on', lambda x: x.start_time)
          ]:
        for note in notes:
          time = get_time(note)
          if time < buffer_size: continue # Skip input sequence
          time = time - buffer_size
          ticks = host.song.to_ticks(time, host.get('output_unit'))
          ticks = int(round(ticks))

          output[-1].append(Message(name,
            note=note.pitch,
            channel=host.get('output_tracks')[i],
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
















## Input Filters
def midotrack2noteseq_performance_rnn(tracks, host):
    seqs = []
    velocity_sensitive = host.get('is_velocity_sensitive')
    coeff = host.get('time_coeff') # Time-stretching coefficient
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
              start_time=last_end_time / coeff,
              end_time=next_start_time / coeff,
              velocity=message.velocity,
              pitch=message.note
              )
          if velocity_sensitive and message.velocity:
            note.velocity = message.velocity
          seqs[-1].append(note)
        last_end_time = next_start_time

    return [NoteSequence(
        notes=seq,
        quantization_info={
            'steps_per_quarter': host.get('steps_per_quarter')},
        tempos=[{ 'time': 0, 'qpm': host.get('bpm') }],
    ) for seq in seqs]


## Output Filters
def noteseq2midotrack_performance_rnn(noteseqs, host):
    output = []
    velocity_sensitive = host.get('is_velocity_sensitive')
    coeff = host.get('time_coeff') # Time-stretching coefficient

    # Convert Notes to Messages
    for i, notes in enumerate(noteseqs):
      track = []
      for (name, get_time) in [
            ('note_off', lambda x: x.end_time),
            ('note_on', lambda x: x.start_time)
          ]:
        for note in notes:
          # print(note)
          time = get_time(note) * 1000
          ticks = host.song.to_ticks(time, host.get('output_unit'))
          ticks = int(round(ticks / 1000))

          track.append(Message(name,
            note=note.pitch,
            channel=host.get('output_tracks')[i],
            velocity=note.velocity if velocity_sensitive else 100,
            time=ticks * coeff
            ))

      if not any(track): continue

      # Sort messages by time
      track.sort(key = lambda msg: msg.time)
      
      # Calculate relative time
      timediff = [track[0].time] + [msg.time for msg in track]
      for i, message in enumerate(track):
        message.time -= timediff[i]

        # FIXME: Returned/Generated messages are too short
        # message.time *= 2
        message.time = int(round(max(0, message.time)))


      output.append(track.copy())

    return output

def mido_no_0_velocity(tracks, host):
    """ 0-velocity messages crash PerformanceRNN
        This filter substitutes 0 velocity by 1
    """
    for track in tracks:
      for msg in track:
        if msg.type in ['note_on', 'note_off'] and msg.velocity == 0:
        # if msg.type in ['note_on'] and msg.velocity == 0:
          msg.velocity = 1
    return tracks


def merge_noteseqs(noteseqs, host, conductor=True):
  steps_per_quarter = host.get('steps_per_quarter')
  # qpm = host.get('bpm')
  output = NoteSequence(
    notes=[note for seq in noteseqs for note in seq.notes[1:]],
    quantization_info={
      'steps_per_quarter': steps_per_quarter,
    },
    tempos=[{ 'time': 0, 'qpm': 120 }],
  )
  output.notes.sort(key=lambda x: x.start_time)
  return [noteseqs[0], output]

filters = {
  # Input (Mido)
  'midotrack2noteseq': midotrack2noteseq,
  'midotrack2pianoroll': midotrack2pianoroll,
  'mido_no_0_velocity': mido_no_0_velocity,
  'midotrack2noteseq_performance_rnn': midotrack2noteseq_performance_rnn,
  'merge_noteseqs': merge_noteseqs,
  

  # Output
  'drop_input_length': drop_input_length,
  'noteseq2midotrack': noteseq2midotrack,
  # 'noteseq2pianoroll': noteseq2pianoroll,
  # 'pianoroll2midotrack': pianoroll2midotrack,
  'mido_track_sort_by_time': mido_track_sort_by_time,
  'mido_track_subtract_last_time': mido_track_subtract_last_time,
  'noteseq2midotrack_performance_rnn': noteseq2midotrack_performance_rnn,

  # Logging
  'print_noteseqs': print_noteseqs,
}


