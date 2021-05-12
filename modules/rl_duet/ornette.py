from argparse import Namespace
import glog as log
import os
import argparse
import torch
import pickle
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
INIT_LEN = 32
SEGMENT_LEN = 64

class RCNNAtt(nn.Module):
    def __init__(self, args):
        super(RCNNAtt, self).__init__()
        self.encoder = nn.Embedding(args.num_pitches, 128)
        self.meta_encoder = nn.Embedding(4, 64)
        self.partner_rnn = nn.GRU(128, 128, 2, bidirectional=True, batch_first=True)
        self.self_rnn = self.partner_rnn
        self.meta_rnn = nn.GRU(64, 64, 1, bidirectional=True, batch_first=True)
        self.conv = nn.Conv1d(in_channels=128 * 4 + 64 * 2, out_channels=64, kernel_size=5, stride=1, padding=2)
        self.attn = nn.Linear(64, 4)
        self.meta_fc = nn.Linear(64, 64)
        self.fc = nn.Linear(64*(2+4) + 64, 256)
        self.pred = nn.Linear(256, args.num_pitches)
        self.args = args

    def forward(self, self_left, partner_left, meta_left_, meta_central_):
        self_left = self.encoder(self_left)
        self_left, _ = self.self_rnn(self_left)

        partner_left = self.encoder(partner_left)
        partner_left, _ = self.partner_rnn(partner_left)

        meta_left_ = meta_left_.reshape(meta_left_.shape[0], meta_left_.shape[1])
        meta_left = self.meta_encoder(meta_left_)
        meta_left, _ = self.meta_rnn(meta_left)

        left_feature = torch.cat([self_left, partner_left, meta_left], dim=2)
        left_feature = left_feature.transpose(1, 2)
        left_feature = self.conv(left_feature)  # [batch, nchan, len]
        max_pool = F.max_pool1d(left_feature, kernel_size=left_feature.shape[2]).view(left_feature.shape[0], -1)  # [batch, nchan]
        avg_pool = F.avg_pool1d(left_feature, kernel_size=left_feature.shape[2]).view(left_feature.shape[0], -1)  # [batch, nchan]
        left_feature = left_feature.transpose(1, 2)  # [batch, len, nchan]
        attn = self.attn(left_feature)  # [batch, len, n_att]
        attn = F.softmax(attn, dim=1).unsqueeze(-2)  # [batch, len, 1, n_att]
        attn_out = (left_feature.unsqueeze(-1) * attn).sum(1)  # [batch, nchan, n_att]
        attn_out = attn_out.view(attn_out.shape[0], -1)

        meta_central_ = meta_central_.reshape(meta_central_.shape[0])
        meta_central = self.meta_encoder(meta_central_)
        meta_fc = F.dropout(F.relu(self.meta_fc(meta_central)))
        concat_out = torch.cat((max_pool, avg_pool, attn_out, meta_fc), dim=1)
        out = self.pred(F.dropout(F.relu(self.fc(concat_out))))
        return out




class OrnetteModule():
    def __init__(self, host, checkpoint='rl_duet'):
      i2p, p2i, _ = pickle.load(open('/ckpt/meta.info', 'rb'))
      args = Namespace(**{})
      args.num_pitches = len(i2p)
      args.index2pitch = i2p
      args.pitch2index = p2i
      model = RCNNAtt(args)
      model.load_state_dict(torch.load(f'/ckpt/{checkpoint}', map_location="cpu"), False)
      model = model.cpu()
      model.eval()
      self.pitch2index = p2i
      self.index2pitch = i2p
      self.model = model
      self.host = host
      self.host.set('generation_unit', 'beats')
      self.host.set('missing_beats', 16)
      self.host.set('steps_per_quarter', 4)
      self.host.set('voices', [0,1,2])
      self.host.set('history', [[] for x in range(3)])

    def generate(self, history=None, length_steps=4, voices=[]):
      music = self.sample_(self.model,
        np.array(history[0]),
        np.array(history[1]),
        np.array(history[2]),
        self.pitch2index['rest'],length_steps)

      music = [list(v) for v in music]
      sig = 4
      meta = [i % sig for i in range(len(music[0]))]
      return [*music, meta]


    def sample_(self, model, own_voice, partner, meta, start_pad, length=16):
      init_len = max(len(x) for x in [own_voice,partner])
      if init_len < SEGMENT_LEN:
          pad_length = SEGMENT_LEN - init_len
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
      
      pulses = self.host.get('time_signature_numerator')
      while pred_ind < SEGMENT_LEN + length:
          start = max(0, pred_ind-SEGMENT_LEN)

          # FIXME: Out of bounds here
          pred_ = pred[start:pred_ind].unsqueeze(0)
          partner_ = partner[start:pred_ind].unsqueeze(0)

          meta_ = meta[start:pred_ind].unsqueeze(0).clone()
          meta_central = meta[INIT_LEN].unsqueeze(0).clone()

          pitch = model(pred_, partner_, meta_, meta_central)
          prob = F.softmax(pitch, dim=1)
          action = prob.multinomial(num_samples=1).data

          pred = torch.cat((pred, action.view(-1)))
          partner = torch.cat((partner, action.view(-1))) # WIP
          meta = torch.cat((meta, meta[pred_ind - pulses].unsqueeze(0))) # WIP
          pred_ind += 1

      if init_len < SEGMENT_LEN:
          pad_len = SEGMENT_LEN - init_len
          partner = partner[pad_len:]
          pred = pred[pad_len:]
      music = [partner.data.cpu().numpy(), pred.data.cpu().numpy()]
      return music

    def decode(self, token):
      print(token)
      step_length = 1 / self.host.get('steps_per_quarter')
      if token == self.pitch2index['rest']:
        return [('note_off', 92, 127, step_length)]

      pitch = self.index2pitch[token]
      if len(pitch.split('_')) > 1:
        return [('note_off', 92, 127, step_length)]

      note = int(self.index2pitch[token])
      return [('note_on', note, 127, step_length)]

    def encode(self, message):
      return message.note

    def close(self):
      return None