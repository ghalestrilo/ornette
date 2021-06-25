from mido import Message

def midotrack2notearray(tracks, host):
  return [[msg.note for msg in track] for track in tracks]

def notearray2midotrack(notearrays, host):
  step_length = 1 / host.get('steps_per_quarter')

  output = []
  for notearray, i in enumerate(notearrays):
    output.append([])

    for token in notearray:
      if token == host.model.pitch2index['rest']:
        return [('note_off', 92, 127, step_length)]

      pitch = host.model.index2pitch[token]
      if len(pitch.split('_')) > 1:
        pitch = pitch.split('_')[0]
        output[-1].append(Message('note_off',
            note=int(pitch),
            channel=host.get('voices')[i],
            velocity=127,
            time=step_length
            ))
        continue

      note = int(host.model.index2pitch[token])

      output[-1].append(Message('note_on',
            note=note,
            channel=host.get('voices')[i],
            velocity=127,
            time=step_length
            ))

      output[-1].append(Message('note_off',
            note=note,
            channel=host.get('voices')[i],
            velocity=127,
            time=0
            ))

  return midotrack2notearray


filters = {
  # Input
  'midotrack2notearray': midotrack2notearray,

  # Output
  'notearray2midotrack': notearray2midotrack
}