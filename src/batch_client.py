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
    self.wait()

  def play(self,note):
    self.send_message('/play', [note + 40])

  def run(self,filename):
    self.set('output_filename', filename)
    self.start() # TODO: on host: unset 'batch_complete'
    self.wait()

  def reset(self):
    self.send_message('/reset', [])
  
  def pause(self):
    self.send_message('/pause', [])

  def end(self):
    self.send_message('/end', [])

  def generate(self, length, unit):
    self.send_message('/generate', [length, unit])
    self.wait()

  def wait(self):
    print("Waiting...")
    self.server.serve_forever()
    print("OK!")