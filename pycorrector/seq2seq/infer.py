# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: 
"""
import sys

import numpy as np
import torch

sys.path.append('../..')

from pycorrector.seq2seq import config
from pycorrector.seq2seq.data_reader import SOS_TOKEN, EOS_TOKEN
from pycorrector.seq2seq.data_reader import load_word_dict
from pycorrector.seq2seq.seq2seq import Seq2Seq
from pycorrector.seq2seq.convseq2seq import ConvSeq2Seq
from pycorrector.seq2seq.data_reader import PAD_TOKEN

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print('device: %s' % device)


class Inference(object):
    def __init__(self, arch, model_path, src_vocab_path, trg_vocab_path,
                 embed_size=50, hidden_size=50, dropout=0.5, max_length=128):
        self.src_2_ids = load_word_dict(src_vocab_path)
        self.trg_2_ids = load_word_dict(trg_vocab_path)
        self.id_2_trgs = {v: k for k, v in self.trg_2_ids.items()}
        if arch == 'seq2seq':
            self.model = Seq2Seq(encoder_vocab_size=len(self.src_2_ids),
                                 decoder_vocab_size=len(self.trg_2_ids),
                                 embed_size=embed_size,
                                 enc_hidden_size=hidden_size,
                                 dec_hidden_size=hidden_size,
                                 dropout=dropout).to(device)
        else:
            trg_pad_idx = self.trg_2_ids[PAD_TOKEN]
            self.model = ConvSeq2Seq(encoder_vocab_size=len(self.src_2_ids),
                                     decoder_vocab_size=len(self.trg_2_ids),
                                     embed_size=embed_size,
                                     enc_hidden_size=hidden_size,
                                     dec_hidden_size=hidden_size,
                                     dropout=dropout,
                                     trg_pad_idx=trg_pad_idx,
                                     device=device,
                                     max_length=max_length).to(device)
        self.model.load_state_dict(torch.load(model_path))
        self.arch = arch
        self.max_length = max_length

    def predict(self, query):
        result = []
        tokens = [token.lower() for token in query]
        tokens = [SOS_TOKEN] + tokens + [EOS_TOKEN]
        src_ids = [self.src_2_ids[i] for i in tokens if i in self.src_2_ids]

        sos_idx = torch.Tensor([[self.trg_2_ids[SOS_TOKEN]]]).long().to(device)
        if self.arch == 'seq2seq':
            src_tensor = torch.from_numpy(np.array(src_ids).reshape(1, -1)).long().to(device)
            src_tensor_len = torch.from_numpy(np.array([len(src_ids)])).long().to(device)
            translation, attn = self.model.translate(src_tensor, src_tensor_len, sos_idx, self.max_length)
            translation = [self.id_2_trgs[i] for i in translation.data.cpu().numpy().reshape(-1) if i in self.id_2_trgs]
        else:
            src_tensor = torch.LongTensor(src_ids).unsqueeze(0).to(device)
            translation, attn = self.model.translate(src_tensor, sos_idx)
            translation = [self.id_2_trgs[i] for i in translation if i in self.id_2_trgs]

        for word in translation:
            if word != EOS_TOKEN:
                result.append(word)
            else:
                break
        return ''.join(result)


if __name__ == "__main__":
    m = Inference(config.arch,
                  config.model_path,
                  config.src_vocab_path,
                  config.trg_vocab_path,
                  embed_size=config.embed_size,
                  hidden_size=config.hidden_size,
                  dropout=config.dropout,
                  max_length=config.max_length
                  )
    inputs = [
        '我现在好得多了。',
        '这几年前时间，',
        '歌曲使人的感到快乐，',
        '会能够大幅减少互相抱怨的情况。'
    ]
    for id, q in enumerate(inputs):
        print(q)
        print(m.predict(q))
        print()
# result:
# input:由我起开始做。
# output:我开始做。
# input:没有解决这个问题，
# output:没有解决的问题，
# input:由我起开始做。
