from pythonosc import udp_client, osc_server
from pythonosc.dispatcher import Dispatcher

class BatchClient(udp_client.SimpleUDPClient):
  def __init__(self, ip, port_out, port_in):
    udp_client.SimpleUDPClient.__init__(self, ip, port_out, port_in)
    dispatcher = Dispatcher()
    dispatcher.map('/ok', lambda _: self.server.shutdown())
    self.server = osc_server.ThreadingOSCUDPServer((ip, port_in), dispatcher)

  def start(self):
    self.send_message('/start', [])

  def stop(self):
    self.send_message('/stop', [])

  def set(self,key,value):
    self.send_message('/set', [key, value])

  def debug(self,key):
    self.send_message('/debug', [key])

  def save(self,filename):
    self.send_message('/save', [filename])

  def play(self,note):
    self.send_message('/play', [note + 40])

  def reset(self):
    self.send_message('/reset', [])
  
  def pause(self):
    self.send_message('/pause', [])

  def wait(self):
    self.server.serve_forever()