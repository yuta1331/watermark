#! usr/bin/env python
# -*- coding: utf-8 -*-

import api
from watermark import detector
import consts

import pickle

########### config ############

ORIGIN_FILE = consts.ORIGIN_FILE
MODIFIED_FILE = consts.MODIFIED_FILE
META_DICT_PICKLE = consts.META_DICT_PICKLE
METHOD = consts.METHOD
ATTR_LIST = consts.ATTR_LIST
SENSITIVE = consts.SENSITIVE
GROUP_BY_ATTR = consts.GROUP_BY_ATTR
WATER_LEN = consts.WATER_LEN
MAX_BIN = consts.MAX_BIN

########### initial ############
_, origin_l = api.parsed_list(ORIGIN_FILE, header=True)
_, modified_l = api.parsed_list(MODIFIED_FILE, header=True)

with open(META_DICT_PICKLE, 'rb') as f:
    meta_dict = pickle.load(f)

# GROUP_BY_ATTRの番地
group_by = [ATTR_LIST.index(attr) for attr in GROUP_BY_ATTR]

########### detection ############
detected_bin = detector(origin_l, modified_l, MAX_BIN, meta_dict,
                        ATTR_LIST, group_by, WATER_LEN, METHOD)

print('###### detected_bin ######')
print(detected_bin)
print('len: ', len(detected_bin))


########### check ###########
WATERMARK_PICKLE = consts.WATERMARK_PICKLE
with open(WATERMARK_PICKLE, 'rb') as f:
    watermarked_bin = pickle.load(f)
print('###### watermarked_bin ######')
print(watermarked_bin)
print('len: ', len(watermarked_bin))

bin_similarity = sum([w == d for w, d in zip(watermarked_bin, detected_bin)])\
                 / WATER_LEN\
                 * 100

print('similarity of bin is {0} %'.format(bin_similarity))
