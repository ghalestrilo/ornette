from argparse import Namespace
import glog as log
import os
import argparse
import torch
# from music21 import midi
import pickle
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
# from model import RCNNAtta
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