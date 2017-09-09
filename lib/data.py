# -*- coding: utf-8 -*-


"""
data processing library
__author__ = 'Jamie (krikit@naver.com)'
__copyright__ = 'No copyright. Just copyleft!'
"""


###########
# imports #
###########
import codecs
from collections import defaultdict
import torch
import torch.utils.data


#########
# types #
#########
class NerDataset(torch.utils.data.Dataset):
    """
    part-of-speech tag dataset
    """
    def __init__(self, fin, voca):
        """
        :param  fin:  input file
        :param  voca:  in/out vocabulary
        """
        self.fin = fin
        self.voca = voca
        self.data_ = []
        self.sent_seps = []    # word separator positions
        self._load()

    def _load(self):
        """
        load data file
        """
        for line in self.fin:
            line = line.rstrip('\r\n')
            if not line:
                self.sent_seps.append(len(self.data_))
                continue
            out_label, in_context = line.split('\t')
            self.data_.append((self.voca['out'][out_label],
                               torch.LongTensor([self.voca['in'][_] for _ in in_context.split()])))

    def __len__(self):
        return len(self.data_)

    def __getitem__(self, idx):
        return self.data_[idx]

    def all(self):
        """
        return all data
        :return:  (labels, features) pair
        """
        return torch.LongTensor([label for label, _ in self.data_]), \
               torch.stack([context for _, context in self.data_])

    def sents(self):
        """
        get sentences (generator)
        :yield:  sentence
        """
        begin = 0
        for end in self.sent_seps:
            if end > begin:
                yield torch.LongTensor([label for label, _ in self.data_[begin:end]]), \
                      torch.stack([context for _, context in self.data_[begin:end]])
            begin = end


#############
# functions #
#############
def load_voca(dir_):
    """
    load input/output vocabularies
    :param  dir_:  where vocabulary files are
    :return:  (in, out) vocabulary pair
    """
    def _load_voca_inner(path, unk=False):
        """
        load vocabulary from file
        :param  path:  file path
        :param  unk:  set unknown as 0 or not
        :return:  (vocabulary, inverted vocabulary) pair
        """
        voca = {}    # string to number
        if unk:
            voca = defaultdict(int)
            voca['<unk/>'] = 0
        acov = []    # number to string
        for line in codecs.open(path, 'r', encoding='UTF-8'):
            line = line.rstrip('\r\n')
            if not line:
                continue
            if line in voca:
                continue
            voca[line] = len(voca)
            acov.append(line)
        return voca, acov

    voca_dic = {}
    for name in ['in', 'out']:
        voca, acov = _load_voca_inner('%s/voca.%s' % (dir_, name), name == 'in')
        voca_dic[name] = voca
        voca_dic[name[::-1]] = acov
    return voca_dic


def load_data(path_pfx, voca):
    """
    load training/dev/test data
    :param  path_pfx:  path prefix
    :param  voca:  vocabulary
    :return:  (dev, test, train) dataset triple
    """
    fins = [(name, codecs.open('%s.%s' % (path_pfx, name), 'r', encoding='UTF-8')) \
            for name in ['dev', 'test', 'train']]
    return {name: NerDataset(fin, voca) for name, fin in fins}