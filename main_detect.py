#! usr/bin/env python
# -*- coding: utf-8 -*-

import api
from watermark import detector

import collections


########### config ############

ORIGIN_FILE = 'anonymized_data.csv'
MODIFIED_FILE = 'watermarked_data.csv'

# METHOD = 'embedding'
METHOD = 'geo'

ATTR_LIST = ['sex', 'tel',
             'poscode', 'addr0', 'addr1', 'addr2', 'addr3', 'addr4',
             'birth', 'time'] # attributes of infile

SENSITIVE = 9
GROUP_BY_ATTR = ['time', 'sex']

WATER_LEN = 256

########### initial ############
csv_header, origin_set = api.parsed_list(ORIGIN_FILE, header=True)
_, modified_set = api.parsed_list(MODIFIED_FILE, header=True)

group_by = [ATTR_LIST.index(attr) for attr in GROUP_BY_ATTR]

########### detection ############
detected_bin = detector(origin_set, modified_set, group_by,
                        ATTR_LIST, WATER_LEN, METHOD)

print(detected_bin)
