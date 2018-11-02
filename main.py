#! usr/bin/env python
# -*- coding: utf-8 -*-

import api
import watermark
import random


########### config ############

infile = '../Anonymizer/anonymized_data.csv'
outfile = 'watermarked_data.csv'

method = 'geo'
embedding_vec = '../practice/neologd.vec'

attr_list = ['sex', 'tel',
             'poscode', 'addr0', 'addr1', 'addr2', 'addr3', 'addr4',
             'birth', 'time']  # attributes of infile

sensitive = 9
group_by_attr = ['time', 'sex']

# 今はrandomな2進数を生成
water_len = 256
water_bin = ''.join([random.choice('01') for i in range(water_len)])
print(water_bin)

########### initial ############
csv_header, dataset = api.parsed_list(infile, True)
group_by = [attr_list.index(attr) for attr in group_by_attr]

########### watermark ############
watermark.watermarker(dataset, group_by, water_bin, attr_list, method)

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
'''
print('#### group_collection ####')
for group in group_collection:
    print(group)
print('num_of_group:  ', len(group_collection))
print('minimun group: ', min(nums_of_each_group))
'''

########### output ############
api.csv_composer(csv_header, dataset, outfile)
