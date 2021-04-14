from pythonosc import udp_client


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
    self.send_message('/start')

  def stop(self):
    self.send_message('/stop')

  def set(self,key,value):
    self.send_message('/set', [key, value])

  def save(self,filename):
    self.send_message('/save', [filename])

  def play(self,note):
    self.send_message('/play', [note + 40])

client = BatchClient(args.ip, args.port)

# 1: Guess test
if (args.experiment in ['all', 'guess']):
  print(f'[guess] Running experiment with model: ...')
  for i in range(0,args.iterations):
      client.play(i)
      print(f'[guess] Iteration {i}')
      # reset history
      # /set buffer_size
      # load (create function, cropping to buffer_size)
  pass

