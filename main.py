#! usr/bin/env python
# -*- coding: utf-8 -*-

import api
import watermark

import random
import pickle


########### config ############

INFILE = 'anonymized_data.csv'
OUTFILE = 'watermarked_data.csv'

WATERMARK = 'pickles/watermark.pkl'

# METHOD = 'embedding'
METHOD = 'geo'

ATTR_LIST = ['sex', 'tel',
             'poscode', 'addr0', 'addr1', 'addr2', 'addr3', 'addr4',
             'birth', 'time']  # attributes of INFILE

SENSITIVE = 9
GROUP_BY_ATTR = ['time', 'tel', 'sex']  # これを元にグループ化

# 今はrandomな2進数を生成
WATER_LEN = 256
WATERMARK_GEN = False

if WATERMARK_GEN is True:
    water_bin = ''.join([random.choice('01') for i in range(WATER_LEN)])
    with open(WATERMARK, 'wb') as f:
        pickle.dump(water_bin, f)
else:
    with open(WATERMARK, 'rb') as f:
        water_bin = pickle.load(f)
print(water_bin)

########### initial ############
csv_header, dataset = api.parsed_list(INFILE, True)

# GROUP_BY_ATTRの番地
group_by = [ATTR_LIST.index(attr) for attr in GROUP_BY_ATTR]

# anonymized dataをソートして保存
dataset = api.sorted_list(dataset, group_by)
api.csv_composer(csv_header, dataset, INFILE)



########### watermark ############
watermark.watermarker(dataset, group_by, water_bin, ATTR_LIST, METHOD)

########### check ############

# 最後尾の要素がグループ内の要素数
# group_collection[i] = [time, sex, num_in_group]
group_collection = list()

# minを使いたいから
nums_of_each_group = list()

for record in dataset:
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

########### output ############
api.csv_composer(csv_header, dataset, OUTFILE)
