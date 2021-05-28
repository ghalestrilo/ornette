from bridge import Bridge
from engine import Engine
from song import Song
from logger import Logger
from store import Store
import mido
import data
from os import environ

class Host:
    def __init__(self,args):
      self.store = Store(self, args)
      self.state = self.store.get_state()
      self.io = Logger(self)
      self.data = data
      self.song = Song(self)
      self.bridge = Bridge(self,args)
      self.engine = Engine(self)
      self.reset()
      self.set('voices', [1])
      self.model = data.load_model(self,args.checkpoint)

      # Notify startup for batch runner
      pass

    def start(self):
      try:
        self.engine.start()
        if (self.state['batch_mode']): self.bridge.notify_task_complete()
        self.bridge.start()
      except KeyboardInterrupt:
          self.close()
          return
      self.close()

    def close(self):
        self.engine.stop()
        self.model.close()
        self.bridge.stop()

    # Host, Song, Engine
    def reset(self):
        self.song.reset()
        self.engine.reset()


    def set(self,field,value,silent=False):
      self.store.set(field,value,silent)
    
    def get(self,field=None):
      return self.store.get(field)


    # TODO: Channel
    def play(self,pitch,instr=None):
      if (instr == None): self.bridge.play(pitch)
      else: self.bridge.play(pitch, instr)



    # Batch (depr)
    def task_ended(self):
      did_it_end = len(self.song.get_voice()) >= self.get('buffer_length')
      return did_it_end
