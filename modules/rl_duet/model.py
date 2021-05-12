import torch
import torch.nn as nn
import torch.nn.functional as F


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


