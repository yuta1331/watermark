#! usr/bin/env python
# -*- coding: utf-8 -*-

import api
from watermark import watermarker
from watermark import detector
from evaluation.IL_calc import IL_calc
from subset.addr_operation import local_addr2formatsgeos as la2fg

import random
import pickle
from copy import deepcopy
import numpy as np
from collections import OrderedDict



########### config ############

INFILE = 'csvs/anonymized_data.csv'
WATERMARK_PICKLE = 'pickles/watermarks.pkl'
META_DICT_PICKLE = 'pickles/meta_dicts.pkl'
METHOD = 'geo'
ATTR_LIST = ['sex', 'tel',
             'poscode', 'addr0', 'addr1', 'addr2', 'addr3', 'addr4',
             'birth', 'time']
SENSITIVE = 9
GROUP_BY_ATTR = ['time', 'tel', 'sex']
WATER_LEN = list(range(50, 1050, 50))
MAX_BIN = 100

WATERMARK_GEN = True
IS_ORIGIN_FILE_SORTED = True
IS_META_DICT_GENERATED = False

TRIAL_NUM = 10
IL_RESULT_PICKLE = 'result/IL_results_embedding_1000.pkl'

if WATERMARK_GEN is True:
    water_bins_dict = OrderedDict()
    for water_len in WATER_LEN:
        water_bins_dict[water_len] = list()
        for i in range(TRIAL_NUM):  # 試行回数
            water_bins_dict[water_len].append(
                    ''.join([random.choice('01') for i in range(water_len)]))
    with open(WATERMARK_PICKLE, 'wb') as f:
        pickle.dump(water_bins_dict, f)
else:
    with open(WATERMARK_PICKLE, 'rb') as f:
        water_bins_dict = pickle.load(f)

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
if 'seq' not in ATTR_LIST:
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

# localized dictionaries
local_addr2formats, local_addr2geos =\
    la2fg(ATTR_LIST, ano_list, addr2formats, addr2geos)

########### watermark ############
IL_dict = OrderedDict()  # {water_len: [ILs]}

tmp_ano_list = deepcopy(ano_list)
IL_list, anonym_addr_l = IL_calc(org_list,
                                 tmp_ano_list,
                                 tmp_ano_list,
                                 ATTR_LIST,
                                 local_addr2formats,
                                 local_addr2geos)
IL = np.mean(IL_list)
IL_dict[0] = [IL for i in range(TRIAL_NUM)]

for water_len in water_bins_dict.keys():
    IL_dict[water_len] = list()

    for water_bin in water_bins_dict[water_len]:
        # print('water_len:', water_len)
        datalist = deepcopy(ano_list)
        meta_dict = None
        meta_dict = watermarker(datalist, water_bin, MAX_BIN,
                                meta_dict, ATTR_LIST, group_by, METHOD)

        detected_bin = detector(ano_list, datalist, MAX_BIN, meta_dict,
                                ATTR_LIST, group_by, water_len, METHOD)
        if water_bin == detected_bin:
            print('Success')
        else:
            print('Failure..')

        '''
        if IS_META_DICT_GENERATED is False:
            with open(META_DICT_PICKLE, 'wb') as f:
                pickle.dump(meta_dict, f)
        '''

        '''
        for record in datalist:
            while len(record) > len(ATTR_LIST):
                print(record)
                record.pop()
        '''

        tmp_ano_list = deepcopy(ano_list)
        IL_list, anonym_addr_l = IL_calc(org_list,
                                         tmp_ano_list,
                                         datalist,
                                         ATTR_LIST,
                                         local_addr2formats,
                                         local_addr2geos)

        IL_dict[water_len].append(np.mean(IL_list))

with open(IL_RESULT_PICKLE, 'wb') as f:
    pickle.dump(IL_dict, f)
