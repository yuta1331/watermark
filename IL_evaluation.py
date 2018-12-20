#! usr/bin/env python
# -*- coding: utf-8 -*-

import api
from watermark import watermarker
import consts
from evaluation.IL_calc import IL_calc

import random
import pickle
from copy import deepcopy
import numpy as np



########### config ############

INFILE = consts.ORIGIN_FILE
OUTFILE = consts.MODIFIED_FILE
WATERMARK_PICKLE = 'pickles/watermarks.pkl'
META_DICT_PICKLE = 'pickles/meta_dicts.pkl'
METHOD = consts.METHOD
ATTR_LIST = consts.ATTR_LIST
SENSITIVE = consts.SENSITIVE
GROUP_BY_ATTR = consts.GROUP_BY_ATTR
WATER_LEN = list(range(10, 100, 10))
MAX_BIN = 100

WATERMARK_GEN = False
IS_ORIGIN_FILE_SORTED = True
IS_META_DICT_GENERATED = False

if WATERMARK_GEN is True:
    water_bins_dict = dict()
    for water_len in WATER_LEN:
        water_bins_dict[water_len] = list()
        for i in range(50):  # 試行回数
            water_bins_dict[water_len].append(
                    ''.join([random.choice('01') for i in range(water_len)]))
    with open(WATERMARK_PICKLE, 'wb') as f:
        pickle.dump(water_bins_dict, f)
else:
    with open(WATERMARK_PICKLE, 'rb') as f:
        water_bins_dict = pickle.load(f)
print(water_bins_dict[10])

if IS_META_DICT_GENERATED is True:
    with open(META_DICT_PICKLE) as f:
        meta_dict = pickle.load(f)
else:
    meta_dict = None

########### initial ############
ORIGINAL_FILE = 'evaluation/original_data.csv'
_, org_list = api.parsed_list(ORIGINAL_FILE, True)

csv_header, ano_list = api.parsed_list(INFILE, True)
datalist = deepcopy(ano_list)

# sequential number の準備
seq_index = csv_header.index('seq')
ATTR_LIST.insert(seq_index, 'seq')

# GROUP_BY_ATTRの番地
group_by = [ATTR_LIST.index(attr) for attr in GROUP_BY_ATTR]

# anonymized dataをソートして保存
if IS_ORIGIN_FILE_SORTED is False:
    datalist = api.sorted_list(datalist, group_by)
    api.csv_composer(csv_header, datalist, INFILE)

with open('pickles/addr2format.pkl', 'rb') as f:
    addr2formats = pickle.load(f)
with open('pickles/addr2geo.pkl', 'rb') as f:
    addr2geos = pickle.load(f)

########### watermark ############
for water_len in water_bins_dict.keys():
    for water_bin in water_bins_dict[water_len]:
        datalist = deepcopy(ano_list)
        meta_dict = watermarker(datalist, water_bin, MAX_BIN,
                                meta_dict, ATTR_LIST, group_by, METHOD)

        if IS_META_DICT_GENERATED is False:
            with open(META_DICT_PICKLE, 'wb') as f:
                pickle.dump(meta_dict, f)

        IL_list, anonym_addr_l = IL_calc(deepcopy(org_list),
                                         deepcopy(ano_list),
                                         deepcopy(datalist),
                                         ATTR_LIST,
                                         addr2formats,
                                         addr2geos)

        print(np.mean(IL_list))
