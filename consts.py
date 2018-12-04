#! usr/bin/env python
# -*- coding: utf-8 -*-

ORIGIN_FILE = 'anonymized_data.csv'
MODIFIED_FILE = 'watermarked_data.csv'

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
MAX_BIN = 3  # 各値につき最大の埋め込みビット
