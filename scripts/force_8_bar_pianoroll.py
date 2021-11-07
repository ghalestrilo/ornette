import mido, os


folders = os.listdir('output/preprocessed/generation') 
folders = [f for f in folders if 'pianoroll' in f]

magic = 15359

def crop_file(filename):
  # print(path)
  midin = mido.MidiFile(filename)
  midout = mido.MidiFile()

  tempo = [msg.tempo for msg in midin if msg.type == 'set_tempo']
  tempo = tempo[0] if any(tempo) else 500000

  for track in midin.tracks:
    ticksum = 0
    midout.tracks.append(mido.MidiTrack())
    for msg in track:
      if hasattr(msg,'time'):
        if msg.time + ticksum > magic: break
        ticksum += msg.time
      midout.tracks[-1].append(msg.copy())
      # print(ticksum)
      
  timee = mido.second2tick(midout.length,midin.ticks_per_beat,tempo)
  if timee > 32000:
    print(filename)
    print(timee)
  # print(midout.length)
  midout.save(filename)

for f in folders:
  # print(f)
  path = f'/home/ghales/git/tg-server/output/preprocessed/generation/{f}'
  for file_ in os.listdir(path):
    crop_file(f'{path}/{file_}')
