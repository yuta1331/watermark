#! usr/bin/env python
# -*- coding: utf-8 -*-

import api
from watermark import watermarker
from subset import embedding_operation
from subset import turbo
from subset import aes_ECB
import consts

import random, string
import pickle


########### config ############

INFILE = consts.ORIGIN_FILE
OUTFILE = consts.MODIFIED_FILE
WATERMARK_PICKLE = consts.WATERMARK_PICKLE
META_DICT_PICKLE = consts.META_DICT_PICKLE
AES_KEY_PICKLE = consts.AES_KEY_PICKLE
METHOD = consts.METHOD
ATTR_LIST = consts.ATTR_LIST
SENSITIVE = consts.SENSITIVE
GROUP_BY_ATTR = consts.GROUP_BY_ATTR
WATER_BYTE = consts.WATER_BYTE
MAX_BIN = consts.MAX_BIN

WATERMARK_GEN = False
AES_KEY_GEN = True
IS_ORIGIN_FILE_SORTED = True
IS_META_DICT_GENERATED = False

# watermarkの準備
if WATERMARK_GEN:
    watermark = ''.join(random.choices(
                            string.ascii_letters
                            + string.digits, k=WATER_BYTE)
                        )
    with open(WATERMARK_PICKLE, 'wb') as f:
        pickle.dump(watermark, f)
else:
    with open(WATERMARK_PICKLE, 'rb') as f:
        watermark = pickle.load(f)
print(watermark)

# AES key generate
if AES_KEY_GEN:
    aes_key = aes_ECB.generate_key()
    with open(AES_KEY_PICKLE, 'wb') as f:
        pickle.dump(aes_key, f)
else:
    with open(AES_KEY_PICKLE, 'rb') as f:
        aes_key = pickle.load(f)

# meta_dict
if IS_META_DICT_GENERATED:
    with open(META_DICT_PICKLE) as f:
        meta_dict = pickle.load(f)
else:
    meta_dict = None

########### initial ############
csv_header, datalist = api.parsed_list(INFILE, True)

# sequential number の準備
seq_index = csv_header.index('seq')
ATTR_LIST.insert(seq_index, 'seq')

# GROUP_BY_ATTRの番地
group_by = [ATTR_LIST.index(attr) for attr in GROUP_BY_ATTR]

# anonymized dataをソートして保存
if IS_ORIGIN_FILE_SORTED is False:
    datalist = api.sorted_list(datalist, group_by)
    api.csv_composer(csv_header, datalist, INFILE)

# embedding mode
if consts.IS_EMBEDDING:
    model = embedding_operation.load_model(consts.MODEL)
else:
    model = None

########### AES encryption ###########
cipher = aes_ECB.AESCipher(aes_key)
water_bin = cipher.encrypt(watermark)
print('encrypted')
print(water_bin)

########### turbo encoding ###########
water_bin = water_bin + turbo.return_punctured_code(water_bin)
print('encoded')
print(water_bin)

########### watermark ############
meta_dict = watermarker(datalist, water_bin, MAX_BIN, meta_dict,
                        ATTR_LIST, group_by, METHOD, model)

if IS_META_DICT_GENERATED is False:
    with open(META_DICT_PICKLE, 'wb') as f:
        pickle.dump(meta_dict, f)

########### check ############

# meta_dict = {group_i: i2b_dict}
# i2b_dict = {_i: embed_num}
embed_sum = 0
keys = list(meta_dict.keys())
for i, meta in enumerate(meta_dict.values()):
    # print('{:<3}'.format(keys[i]), meta)
    if consts.MODE == 'proposal':
        for embed_num in meta.values():
            embed_sum += embed_num
    if consts.MODE == 'existing':
        embed_sum += meta
print('embeded num: ', embed_sum)

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
