import mido
import os, subprocess, sys
import shutil


# TODO: In the future, use this through ornette, inside docker containers for: 1. preprocessing and 2. extraction
sys.path.append(os.path.abspath(os.path.join('server')))

preprocess_scriptdir = os.path.abspath(os.path.join(os.path.pardir, 'miditools'))
preprocess_script = os.path.join(preprocess_scriptdir, 'midisox_py') 
# preprocess_script = os.path.join(preprocess_scriptdir, 'test_py')

sample_length = 16
write = print


import random

# # Script Information
script_output_bpm = 60
desired_bars = sample_length # 16
desired_seconds = desired_bars * (60/script_output_bpm) # 32


def runscript(script, cwd=os.path.curdir):
  write(f'running: {" ".join(script)}')
  # result = subprocess.run(script, capture_output=True, text=True).stdout
  result = subprocess.run(script, capture_output=True,cwd=cwd)
  if result.stdout: print(result.stdout.decode('utf8'))
  if result.stderr: print(result.stderr.decode('utf8'))

def preprocess(_in, _out, logfile=None, trim_start = -1, desired_seconds=desired_seconds,cwd=preprocess_scriptdir):
    """ Midi files are time warped to 120bpm to make time calculations more reliable """
    tmpfile = os.path.abspath('/tmp/prepmid')
    _in = os.path.abspath(_in)
    _out = os.path.abspath(_out)
    target_seconds = desired_seconds

    # Get basic song info
    if os.path.exists(tmpfile): os.remove(tmpfile)
    mid = mido.MidiFile(_in)
    tempo = next(msg for msg in mid if msg.type == 'set_tempo').tempo
    bpm = mido.tempo2bpm(tempo)
    
    # Define scripts to run
    prepscript = lambda *params: ['python3', preprocess_script] + [*params]
    trim = lambda _start: runscript(prepscript('-m', tmpfile, _out, 'trim', str(_start), str(target_seconds)),cwd=cwd)

    # Initialize tmp file
    # shutil.copy(_in,tmpfile)
    # runscript(prepscript(_in, tmpfile, 'stat'))
    # We could pre-trim the file here?
    print(prepscript(_in, tmpfile, 'trim', str(0), '90'))
    runscript(prepscript(_in, tmpfile, 'trim', str(0), '90'),cwd=cwd) # Cut 1:30 from the song
    # runscript(prepscript(tmpfile, tmpfile, 'tempo', str(120/bpm)))
    _mid = mido.MidiFile(tmpfile)
    for i, track in enumerate(_mid.tracks[1:]):
      for msg in track[:40]:
        if not msg.type.startswith('note'):
          _mid.tracks[1+i].remove(msg)
    _mid.save(tmpfile)

    # Seek for a contiguous part
    search_threshold = min(mid.length, 100)
    best_length = 0
    best_start = 0
    best_diff = abs(best_length - target_seconds)
    delta = 0.5
    # diff = abs(best_length - target_seconds)
    # while best_length < target_seconds:
    trim_start = max(trim_start,0)
    while best_diff > delta:
        trim(trim_start)
        mid_out = mido.MidiFile(_out)
        diff = abs(mid_out.length - target_seconds)

        # Detect longest contiguous segment
        if diff < best_diff:
          best_length = mid_out.length
          best_start = trim_start
        
        if diff < delta: break

        # If all file was consumed
        
        # if trim_start + mid_out.length > search_threshold:
        if trim_start + mid_out.length > search_threshold:
            # write(f'No contiguous {target_seconds}s segment in {_out}')
            trim_start = best_start
            trim(trim_start)

            missing_seconds = target_seconds - best_length

            if missing_seconds > 0:
              # write(f'needs {missing_seconds} seconds')
              runscript(prepscript(_out, _out, 'pad', '0', str(missing_seconds)),cwd=cwd)
            break

        trim_start += 1

    # Merging must go at the end. 
    # Otherwise, it will merge data into the conductor and possibly mess up everything
    # runscript(prepscript('-m', _out, _out))
    os.remove(tmpfile)
    mid = mido.MidiFile(_out)
    if 'time_signature' not in map(lambda msg: msg.type, mid):
      mid.tracks[0].insert(1,mido.MetaMessage('time_signature',numerator=4,denominator=4,time=0))
      mid.save(_out)



extraction_scriptdir = os.path.abspath(os.path.join(os.path.pardir, 'mgeval'))
extraction_script = os.path.join(extraction_scriptdir, 'start.sh')
cmd_extraction = lambda dataset_1, dataset_2, output_pickle_filename: [
    'bash',
    extraction_script,
    os.path.abspath(dataset_1),
    os.path.abspath(dataset_2),
    output_pickle_filename,
    str(sample_length)
]

def extract_metrics(folder1, folder2, metricsfile):
  runscript(cmd_extraction(folder1,folder2, metricsfile), extraction_scriptdir)

