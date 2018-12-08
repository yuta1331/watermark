#! usr/bin/env python
# -*- coding: utf-8 -*-

import api
from watermark import watermarker
import consts

import random
import pickle


########### config ############

INFILE = consts.ORIGIN_FILE
OUTFILE = consts.MODIFIED_FILE
WATERMARK = consts.WATERMARK
METHOD = consts.METHOD
ATTR_LIST = consts.ATTR_LIST
SENSITIVE = consts.SENSITIVE
GROUP_BY_ATTR = consts.GROUP_BY_ATTR
WATER_LEN = consts.WATER_LEN
MAX_BIN = consts.MAX_BIN

WATERMARK_GEN = False
IS_ORIGIN_FILE_SORTED = True

if WATERMARK_GEN is True:
    water_bin = ''.join([random.choice('01') for i in range(WATER_LEN)])
    with open(WATERMARK, 'wb') as f:
        pickle.dump(water_bin, f)
else:
    with open(WATERMARK, 'rb') as f:
        water_bin = pickle.load(f)
print(water_bin)

########### initial ############
csv_header, datalist = api.parsed_list(INFILE, True)

# GROUP_BY_ATTRの番地
group_by = [ATTR_LIST.index(attr) for attr in GROUP_BY_ATTR]

# anonymized dataをソートして保存
if IS_ORIGIN_FILE_SORTED is False:
    datalist = api.sorted_list(datalist, group_by)
    api.csv_composer(csv_header, datalist, INFILE)


########### watermark ############
meta_dict = watermarker(datalist, water_bin, MAX_BIN,
                        None, ATTR_LIST, group_by, METHOD)

########### check ############

# meta_dict = {group_i: i2b_dict}
# i2b_dict = {_i: embed_num}
embed_sum = 0
keys = list(meta_dict.keys())
for i, meta in enumerate(meta_dict.values()):
    print('{:<3}'.format(keys[i]), meta)
    for embed_num in meta.values():
        embed_sum += embed_num
print(embed_sum)

'''
# 最後尾の要素がグループ内の要素数
# group_collection[i] = [time, sex, num_in_group]
group_collection = list()

# minを使いたいから
nums_of_each_group = list()

for record in datalist:
    if len(group_collection) == 0:
        group_collection = [[record[i] for i in group_by]]
        group_collection[0].append(1)
    else:
        tmp_list = [record[i] for i in group_by]
        if tmp_list == group_collection[-1][:-1]:
            group_collection[-1][-1] += 1
        else:
            nums_of_each_group.append(group_collection[-1][-1])

            tmp_list.append(1)
            group_collection.append(tmp_list)
print('#### group_collection ####')
for group in group_collection:
    print(group)
print('num_of_group:  ', len(group_collection))
print('minimun group: ', min(nums_of_each_group))
'''

########### output ############
api.csv_composer(csv_header, datalist, OUTFILE)
