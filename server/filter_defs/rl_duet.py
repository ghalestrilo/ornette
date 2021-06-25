from mido import Message

def midotrack2notearray(tracks, host):
  return [[msg.note for msg in track] for track in tracks]

def notearray2midotrack(notearrays, host):
  step_length = 1 / host.get('steps_per_quarter')
  
  print(notearrays)
  output = []
  for i, notearray in enumerate(notearrays):
    output.append([])

    last_voice = output[-1]

    for token in notearray:
      if token == host.model.pitch2index['rest']:
        last_voice.append(
          Message('note_off',
              note=92,
              channel=host.get('voices')[i],
              velocity=127,
              time=step_length
              ))
        continue

      pitch = host.model.index2pitch[token]
      if len(pitch.split('_')) > 1:
        pitch = pitch.split('_')[0]
        last_voice.append(Message('note_off',
            note=int(pitch),
            channel=host.get('voices')[i],
            velocity=127,
            time=step_length
            ))
        continue

      note = int(host.model.index2pitch[token])

      last_voice.append(Message('note_on',
            note=note,
            channel=host.get('voices')[i],
            velocity=127,
            time=step_length
            ))

      last_voice.append(Message('note_off',
            note=note,
            channel=host.get('voices')[i],
            velocity=127,
            time=0
            ))

  return output


filters = {
  # Input
  'midotrack2notearray': midotrack2notearray,

  # Output
  'notearray2midotrack': notearray2midotrack
}