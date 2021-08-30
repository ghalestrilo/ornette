from note_seq import NoteSequence, PianorollSequence
from note_seq.midi_io import note_sequence_to_pretty_midi
from magenta.music.sequences_lib import is_relative_quantized_sequence, quantize_note_sequence
from mido import MidiFile, Message
from itertools import takewhile, dropwhile

# Magenta Filters

def noteseq_scale(noteseqs, host):
  scaling_factor = host.get('scaling_factor')
  for noteseq in noteseqs:
    for note in noteseq.notes:
      note.start_time *= scaling_factor
      note.end_time *= scaling_factor
  return noteseqs

def print_noteseqs(noteseqs, host, label=""):
  """ Prints a NoteSeq and returns it """
  print(f'[{label}] printing sequences')
  for i, noteseq in enumerate(noteseqs):
    print(f'\n sequence {i}')
    for note in noteseq.notes:
      print(f'pitch: {note.pitch}\t| velocity: {note.velocity}\t| start_time: {note.start_time:.4f}\t| end_time: {note.end_time:.4f}')
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
        not_own_stop = lambda msg: not (msg.type == 'note_off' and msg.note == msg.note)
        ringing_interval = takewhile(not_own_stop, rest)
        own_stop = list(dropwhile(not_own_stop, rest))
        own_stop = own_stop[0].time if len(own_stop) else 0
        # print(list(ringing_interval))
        ringing_interval = map(lambda msg: msg.time, ringing_interval)
        duration = sum(ringing_interval) + own_stop
        # print(f'duration: {duration}')

        # Create Notes
        if not message.is_meta and message.type.startswith('note'):
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
    total_quantized_steps = host.song.convert(host.get('input_length'), host.get('input_unit'), 'beats')
    total_quantized_steps = int(round(total_quantized_steps))

    sequences = [NoteSequence(
        notes=seq.copy(),
        quantization_info={
          'steps_per_quarter': steps_per_quarter,
        },
        tempos=[{ 'time': 0, 'qpm': qpm }],
        total_quantized_steps=total_quantized_steps
    ) for seq in seqs]
    end_times = [note.end_time for track in sequences for note in track.notes] + [0]
    host.set('last_end_time', max(end_times))
    return sequences


def init_default_pitch(noteseqs, host):
  for noteseq in noteseqs:
    if not any(noteseq.notes):
      note = noteseq.notes.add()
      note.start_time = 0
      note.end_time = 0
      note.pitch = host.get('init_pitch')
      note.velocity = 100
  return noteseqs




## Debugging filters

def debug_generation_request(noteseqs, host):
  # buflen = host.song.convert(host.get('output_length'), 'bars', host.get('output_unit'))
  outlen = host.get('generation_requested_beats')
  last_end_time = host.get('last_end_time')
  host.io.log(f'generating interval: [{last_end_time}:{last_end_time + outlen}]')
  return noteseqs







# Trimming Methods

def noteseq_trim_end(noteseqs, host):
  section_end = host.get('generation_requested_beats')
  host.io.log(f'section_end: {section_end}')
  for noteseq in noteseqs:
    rmnotes = []
    for i, note in enumerate(noteseq.notes):
      if note.start_time > section_end:
        rmnotes += [i]
      elif note.end_time > section_end: note.end_time = section_end

    for i in reversed(rmnotes): noteseq.notes.remove(noteseq.notes[i])
  
  return noteseqs


def noteseq_trim_start(noteseqs, host):
  seq_start_time = host.get('last_end_time')

  host.io.log(f'dropping notes before: {seq_start_time}')
  for noteseq in noteseqs:
    if not any(noteseq.notes): continue
    rmnotes = []
    for i, note in enumerate(noteseq.notes):
      note.start_time = round(note.start_time - seq_start_time, 8)
      note.end_time = round(note.end_time - seq_start_time, 8)
      if note.start_time < 0: rmnotes += [i]
    
    for i in reversed(rmnotes): noteseq.notes.remove(noteseq.notes[i])
  return noteseqs











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
          # if time < buffer_size: continue # Skip input sequence
          # time = time - buffer_size
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

from functools import reduce
def _sub_last_time(seq, msg):
  last_msg_time = sum(msg.time for msg in seq)
  numsg = Message(msg.type, note=msg.note, channel=msg.channel, time=msg.time - last_msg_time, velocity=msg.velocity)
  return seq + [numsg]

def mido_track_subtract_previous_time(tracks, host):
  """ Some models save accumulated time instead of note length """
  tracks = [reduce(_sub_last_time, track, []) for track in tracks]
  return tracks


def _shift_time(track):
  times = [0] + [msg.time for msg in track]
  for i, msg in enumerate(track):
    msg.time = times[i]
  return track

def mido_track_add_note_offs(tracks, host):
  _make_note_off = lambda msg: Message('note_off', note=msg.note, channel=msg.channel, time=0, velocity=msg.velocity)
  _add_note_offs = lambda track: [n for sublist in ([note, _make_note_off(note)] for note in track) for n in sublist]
  

  return [_add_note_offs(track) for track in tracks]






def mido_no_0_velocity(tracks, host):
    """ 0-velocity messages crash PerformanceRNN
        This filter substitutes 0 velocity by 1
    """
    for track in tracks:
      for msg in track:
        if msg.type in ['note_on', 'note_off'] and msg.velocity == 0:
        # if msg.type in ['note_on'] and msg.velocity == 0:
          msg.velocity = 100
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
  'mido_no_0_velocity': mido_no_0_velocity,
  'merge_noteseqs': merge_noteseqs,
  'noteseq_scale': noteseq_scale,
  'init_default_pitch': init_default_pitch,

  # Output
  'noteseq_trim_start': noteseq_trim_start,
  'noteseq_trim_end': noteseq_trim_end,
  'noteseq2midotrack': noteseq2midotrack,

  # Default filters
  'mido_track_sort_by_time': mido_track_sort_by_time,
  'mido_track_subtract_previous_time': mido_track_subtract_previous_time,
  'mido_track_add_note_offs': mido_track_add_note_offs,

  # Logging
  'print_noteseqs': print_noteseqs,
  'debug_generation_request': debug_generation_request,
}
