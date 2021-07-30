from mido import Message
import numpy as np

def midotrack2notearray(tracks, host):
  a = [[msg.note for msg in track if not msg.is_meta] for track in tracks]
  return np.array(a)

def notearray2midotrack(notearrays, host):
  step_length = 1 / host.get('steps_per_quarter')
  step_length = host.song.to_ticks(step_length, host.get('output_unit'))
  
  # print(notearrays)
  output = []
  for i, notearray in enumerate(notearrays):
    output.append([])

    last_voice = output[-1]

    for token in notearray:
      if token == host.model.pitch2index['rest']:
        last_voice.append(
          Message('note_off',
              note=92,
              channel=host.get('output_tracks')[i],
              velocity=127,
              time=step_length
              ))
        continue

      pitch = host.model.index2pitch[token]
      if len(pitch.split('_')) > 1:
        pitch = pitch.split('_')[0]
        last_voice.append(Message('note_off',
            note=int(pitch),
            channel=host.get('output_tracks')[i],
            velocity=127,
            time=step_length
            ))
        continue

      note = int(host.model.index2pitch[token])

      last_voice.append(Message('note_on',
            note=note,
            channel=host.get('output_tracks')[i],
            velocity=127,
            time=0
            ))

      last_voice.append(Message('note_off',
            note=note,
            channel=host.get('output_tracks')[i],
            velocity=127,
            time=step_length
            ))

  return output


filters = {
  # Input
  'midotrack2notearray': midotrack2notearray,

  # Output
  'notearray2midotrack': notearray2midotrack
}