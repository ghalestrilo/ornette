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
    def by_start_time(e): return e.start_time if e is not None else []
    def by_end_time(e): return e.end_time if e is not None else []


    output = []
    print(noteseqs)
    for i, seq in enumerate(noteseqs):
      m = MidiFile()
      # notes = seq.notes
      notes = seq
      
      for (name, key, get_time) in [
          ('note_off', by_end_time, lambda x: x.end_time),
          ('note_on', by_start_time, lambda x: x.start_time)
        ]:
        m.add_track(name)
        notes.sort(key=key)
        last_time = 0
        

        for note in notes:
          # host.io.log(f"time:          {get_time(note)}")
          host.io.log(f"last_time:     {last_time}")
          # host.io.log(f"steps/quarter: {host.get('steps_per_quarter')}")
          # host.io.log(f"ticks:         {host.song.to_ticks(get_time(note) * host.get('steps_per_quarter'), 'beats')}")
          

          
          last_time = int(round(last_time + host.song.convert(get_time(note), 'seconds', 'ticks')))
          # last_time = last_time + host.song.to_ticks(get_time(note) * host.get('steps_per_quarter'), 'beats')
          m.tracks[-1].append(Message(name,
            note=note.pitch,
            channel=host.get('voices')[i],
            velocity=note.velocity,
            # time=last_time
            time=last_time
            ))

      output.append([msg for msg in m])
    return output


















def decode(token):
    ''' Must return a mido message array (type (note_on), note, velocity, duration)'''

    start = max(0, token.start_time - self.host.get('last_end_time'))
    end = max(0, token.end_time - token.start_time)
    decoded = [
        ('note_on', token.pitch, token.velocity, start),
        ('note_off', token.pitch, token.velocity, end)
    ]

    self.host.set('last_end_time', max(0, token.end_time))
    return decoded


def encode(message):
    ''' Receives a mido message, must return a model-compatible token '''
    last_end_time = self.host.get('last_end_time')
    next_start_time = last_end_time + \
        self.host.from_ticks(message.time, 'beats')

    note = NoteSequence.Note(
        instrument=0,
        program=0,
        start_time=last_end_time,
        end_time=next_start_time,
        velocity=message.velocity or 1,
        pitch=message.note,
    )

    self.host.set('last_end_time', next_start_time)
    return note
