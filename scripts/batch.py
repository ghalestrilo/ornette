from pythonosc import udp_client


import argparse

parser = argparse.ArgumentParser()

parser.add_argument("--ip",         type=str,  default="127.0.0.1", help="The IP address the ornette host is running on")
parser.add_argument("--port",       type=int,  default=5005,        help="The port to listen on")

parser.add_argument('--state',      type=str,  default="0",         help='the initial state of the improv')

parser.add_argument("--playback",   type=bool, default=True,        help="Use supercollider for sound playback")
parser.add_argument("--batch-mode", type=bool, default=False,       help="Use supercollider for sound playback")

parser.add_argument('--repetitions',type=int,  default=256,         help='maximum buffer length')
parser.add_argument('--experiment', type=str, default='all',        choices=['all', 'guess'], help='Which experiment to run')

args = parser.parse_args()
client = udp_client.SimpleUDPClient(args.ip, args.port)


# 1: Guess test
if (args.experiment in ['all', 'guess']):
  pass

