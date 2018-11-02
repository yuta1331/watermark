#! usr/bin/env python
# -*- coding: utf-8 -*-

import api
from watermark import detector

import collections


########### config ############

origin_file = '../Anonymizer/anonymized_data.csv'
modified_file = 'watermarked_data.csv'

embedding_vec = '../practice/neologd.vec'

attr_list = ['sex', 'tel',
             'poscode', 'addr0', 'addr1', 'addr2', 'addr3', 'addr4',
             'birth', 'time'] # attributes of infile

sensitive = 9
group_by_attr = ['time', 'sex']

water_len = 256

########### initial ############
init_row, origin_set = api.parsed_list(origin_file)
init_row, modified_set = api.parsed_list(modified_file)

group_by = [attr_list.index(attr) for attr in group_by_attr]

########### detection ############
detected_bin = detector(origin_set, modified_set, group_by,
                        attr_list, water_len, embedding_vec)

print(detected_bin)
