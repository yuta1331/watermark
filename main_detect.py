#! usr/bin/env python
# -*- coding: utf-8 -*-

import api
from watermark import detector
from subset import embedding_operation
from subset import turbo
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

# embedding mode
if consts.IS_EMBEDDING:
    model = embedding_operation.load_model(consts.MODEL)
else:
    model = None

########### detection ############
detected_bin = detector(origin_l, modified_l, MAX_BIN, meta_dict,
                        ATTR_LIST, group_by, WATER_LEN*2, METHOD, model)
print(len(detected_bin))

########### turbo decoding ###########
detected_data = detected_bin[:len(detected_bin)//2]
detected_parity = detected_bin[len(detected_bin)//2:]

if consts.IS_USED_AES:
    detected_data += '0'*((128 - (len(detected_bin)//2)%128)%128)

    pad_num = (128 - (len(detected_bin) - len(detected_bin)//2)%128)%128
    detected_parity += '0' *pad_num

data, num_of_loop = turbo.decode(detected_data, detected_parity, 500, True)

print('###### detected_bin ######')
print(data)
print('len: ', len(data))


########### check ###########
WATERMARK_PICKLE = consts.WATERMARK_PICKLE
with open(WATERMARK_PICKLE, 'rb') as f:
    watermarked_bin = pickle.load(f)
print('###### watermarked_bin ######')
print(watermarked_bin)
print('len: ', len(watermarked_bin))

bin_similarity = (sum([w == d for w, d in zip(watermarked_bin, data)])
                  / WATER_LEN
                  * 100)

print('similarity of bin is {0} %'.format(bin_similarity))
