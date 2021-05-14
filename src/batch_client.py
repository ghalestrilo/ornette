from pythonosc import udp_client, osc_server
from pythonosc.dispatcher import Dispatcher

class BatchClient(udp_client.SimpleUDPClient):
  def __init__(self, logger, ip, port_out, port_in):
    udp_client.SimpleUDPClient.__init__(self, ip, port_out, port_in)
    dispatcher = Dispatcher()
    dispatcher.map('/ok', lambda _: self.server.shutdown())
    self.server = osc_server.ThreadingOSCUDPServer((ip, port_in), dispatcher)
    self.log = logger

  def start(self):
    self.send_message('/start', [])

  def stop(self):
    self.send_message('/stop', [])

  def set(self,*args):
    self.send_message('/set', args)

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
    self.log("waiting...")
    self.server.serve_forever()
    self.log("ok!")
  
  def load_bars(self,filename,barcount):
    self.send_message('/load_bars', [filename, barcount])
    self.wait()