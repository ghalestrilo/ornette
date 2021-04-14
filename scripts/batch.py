from pythonosc import udp_client
from time import sleep

import argparse

parser = argparse.ArgumentParser()

parser.add_argument("--ip",         type=str,  default="127.0.0.1", help="The IP address the ornette host is running on")
parser.add_argument("--port",       type=int,  default=5005,        help="The port to listen on")

parser.add_argument('--state',      type=str,  default="0",         help='the initial state of the improv')

parser.add_argument("--playback",   type=bool, default=True,        help="Use supercollider for sound playback")
parser.add_argument("--batch-mode", type=bool, default=False,       help="Use supercollider for sound playback")

parser.add_argument('--iterations', type=int,  default=10,          help='Number of times to run the experiment')
parser.add_argument('--experiment', type=str,  default='all',       choices=['all', 'guess'], help='Which experiment to run')

args = parser.parse_args()




class BatchClient(udp_client.SimpleUDPClient):
  def __init__(self,ip,port):
    udp_client.SimpleUDPClient.__init__(self,ip, port)

  def start(self):
    self.send_message('/start', [])

  def stop(self):
    self.send_message('/stop', [])

  def set(self,key,value):
    self.send_message('/set', [key, value])

  def save(self,filename):
    self.send_message('/save', [filename])

  def play(self,note):
    self.send_message('/play', [note + 40])

  def reset(self):
    self.send_message('/reset', [])
  
  def pause(self):
    self.send_message('/pause', [])

client = BatchClient(args.ip, args.port)

# TODO: Automate this
prompt = 'dataset/vgmidi/labelled/midi/Super Mario_N64_Super Mario 64_Dire Dire Docks.mid'


# EXPERIMENT 1: Guess test
if (args.experiment in ['all', 'guess']):
  print(f'[guess] Running experiment with model: ...')
  client.set('batch_mode', 'True')
  
  for i in range(0,args.iterations):
      print(f'[guess] Iteration {i}')
      client.set('buffer_size', i*10)
      client.reset()
      client.start()
      sleep(4)
      client.pause()
      client.save(f'guess-promptname-{i}') # TODO: Update promptname
      # load (create function, cropping to buffer_size)
  pass

# Algorithm
# Set batch mode
# (outer loop) Set prompt 
# (inner loop) Set buffer size, reset history, set max_output_time
#     Load, crop Prompt (TODO: load function in host, encode function in model)
#     Run Model
#     TODO: Await response? start another server thread?