from note_seq import NoteSequence
from mido import MidiFile, Message

from logging import info

# Magenta Filters


# Input Filters
def midotrack2noteseq(tracks, host):
    seqs = []
    for track in tracks:
      seqs.append([])
      last_end_time = 0
      for message in track:
        next_start_time = last_end_time + host.song.from_ticks(message.time, 'beats')
        if not message.is_meta:
          seqs[-1].append(NoteSequence.Note(
              instrument=0,
              program=0,
              start_time=last_end_time,
              end_time=next_start_time,
              # velocity=message.velocity or 1,
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

# Output Filters


# WIP
def noteseq2midotrack(noteseqs, host):
    # def by_start_time(e): return e.start_time if e is not None else []
    # def by_end_time(e): return e.end_time if e is not None else []


    output = []
    print(noteseqs)
    for i, notes in enumerate(noteseqs):
      # m = MidiFile()

      # for (name, key, get_time) in [
      #     ('note_off', by_end_time, lambda x: x.end_time),
      #     ('note_on', by_start_time, lambda x: x.start_time)
      #   ]:
      #   m.add_track(name)
      #   notes.sort(key=key)
      #   last_time = 0

      #   host.io.log(name)
      #   for note in notes:
      #     # ticks = host.song.convert(get_time(note), 'beats', 'ticks') # host.get('steps_per_quarter')
      #     # last_time = last_time + int(round(ticks))
      #     ticks = host.song.convert(get_time(note), 'beats', 'ticks') # host.get('steps_per_quarter')
      #     # last_time = int(round(ticks))
      #     host.io.log(f"last_time:     {ticks} (+{ticks - last_time})")
          
      #     # last_time = last_time + host.song.to_ticks(get_time(note) * host.get('steps_per_quarter'), 'beats')
      #     m.tracks[-1].append(Message(name,
      #       note=note.pitch,
      #       channel=host.get('voices')[i],
      #       velocity=note.velocity,
      #       time=ticks - last_time
      #       ))
      #     last_time = ticks
      # output.append([msg for msg in m if not msg.is_meta])
    
      output.append([])
      for (name, get_time) in [
            ('note_off', lambda x: x.end_time),
            ('note_on', lambda x: x.start_time)
          ]:
        last_time = 0
        for note in notes:
          ticks = host.song.convert(get_time(note), host.get('output_unit'), 'ticks') # host.get('steps_per_quarter')
          ticks = int(round(ticks))
          host.io.log(f"last_time:     {ticks} (+{ticks - last_time})")
          last_time = ticks

          output[-1].append(Message(name,
            note=note.pitch,
            channel=host.get('voices')[i],
            velocity=note.velocity,
            time=ticks
            ))

    # Sort by start_time
    output[-1].sort(key = lambda msg: msg.time)

    print(output)

    # Adjust note time
    last_time = 0
    for msg in output[-1]:
      dur = msg.time - last_time
      msg.time = dur
      last_time += dur


    host.io.log('output:')
    host.io.log(output)
    return output

