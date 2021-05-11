from argparse import Namespace
import glog as log
import os
import argparse
import torch
# from music21 import midi
import pickle
import torch.nn.functional as F
import numpy as np
from model import RCNNAtt
INIT_LEN = 32
SEGMENT_LEN = 64

class OrnetteModule():
    def __init__(self, host, checkpoint='rl_duet'):
      i2p, p2i, _ = pickle.load(open('datasets/meta.info', 'rb'))
      args = Namespace(**{})
      args.num_pitches = len(i2p)
      args.index2pitch = i2p
      args.pitch2index = p2i
      model = RCNNAtt(args)
      model.load_state_dict(torch.load(checkpoint, map_location="cpu"), False)
      model = model.cpu()
      model.eval()
      self.model = model

    def generate(self, history=None, length_seconds=4):
      own_voice = test_self[i]
      partner = test_partner[i]
      meta = test_meta_old[i]
      start_pad = pitch2index['rest']
      model = self.model

      if INIT_LEN < SEGMENT_LEN:
          pad_length = SEGMENT_LEN - INIT_LEN
          pad = np.full((pad_length,), start_pad)
          own_voice = np.concatenate([pad, own_voice], 0)
          partner = np.concatenate([pad, partner], 0)
          meta_ = [0, 1, 2, 3]
          pad_meta = [meta_[(i - pad_length) % 4] for i in range(pad_length)]
          meta = np.concatenate([pad_meta, meta], 0)
      own_voice = torch.from_numpy(own_voice).cpu().long()
      partner = torch.from_numpy(partner).cpu().long()
      meta = torch.from_numpy(meta).cpu().reshape(len(meta), -1).long()
      pred_ind = SEGMENT_LEN
      pred = own_voice[:pred_ind]
      while pred_ind < len(partner):
          start = max(0, pred_ind-SEGMENT_LEN)
          pitch = model(pred[start:pred_ind].unsqueeze(0),
                        partner[start:pred_ind].unsqueeze(0),
                        meta[start:pred_ind].unsqueeze(0),
                        meta[pred_ind].unsqueeze(0))
          prob = F.softmax(pitch, dim=1)
          action = prob.multinomial(num_samples=1).data
          pred = torch.cat((pred, action.view(-1)))
          pred_ind += 1
      if INIT_LEN < SEGMENT_LEN:
          pad_len = SEGMENT_LEN - INIT_LEN
          partner = partner[pad_len:]
          pred = pred[pad_len:]
      music = [partner.data.cpu().numpy(), pred.data.cpu().numpy()]
      return music

    def decode(self, token):
      return None

    def encode(self, message):
      return None

    def close(self):
      return None