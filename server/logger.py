from pprint import pprint

class Logger:
    def __init__(self, host):
      self.host = host
      self.state = host.state

    

    # TODO: IO
    def log(self, msg):
      # if self.is_debugging(): print(f"[server] {msg}")
      print(f"[server:{self.host.get('module')}] {msg}")

    def print(self, field=None, pretty=True):
      """ Print a key from the host state """
      
      host = self.host
      state = self.state
      if (field == None):
        pprint(state)
        return
      try:
          if (field == 'song'):
            data = self.host.song.data
            self.host.io.log(data)
            for track in data.tracks:
              self.host.io.log(track)

              for msg in track:
                self.host.io.log(f'  {msg}')

            return

          if (field == 'buffer'):
            ticks = self.host.song.to_ticks(16,'bars')
            self.host.io.log(f'debugging 16 bars ({ticks} ticks)')
            data = self.host.song.buffer(ticks)
            self.host.io.log(data)
            for track in data:
              self.host.io.log(track)

              for msg in track:
                self.host.io.log(f'  {msg}')
            return

          if (field == 'time'):
            host.song.time_debug()
            return

          data = state[field]
          if (pretty == True and field == 'history'):
            for voice in data:
              pprint([host.model.decode(e) for e in voice])
            self.log(f'{len(data)} voices total')
            return
          if (pretty == True and field == 'output_data'):
            pprint(data)
            return

          self.log("[{0}] ~ {1}".format(field, data))

      except KeyError:
          self.log("no such key ~ {0}".format(field))
          pass
      #/ TODO: IO

