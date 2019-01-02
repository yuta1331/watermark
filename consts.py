#! usr/bin/env python
# -*- coding: utf-8 -*-

# comparison method
# MODE = 'proposal'
MODE = 'existing'

ORIGIN_FILE = 'csvs/anonymized_data.csv'
MODIFIED_FILE = 'csvs/' + MODE + '_watermarked_data.csv'

WATERMARK_PICKLE = 'pickles/' + MODE + '_watermark.pkl'
META_DICT_PICKLE = 'pickles/' + MODE + '_meta_dict.pkl'

METHOD = 'geo'
IS_EMBEDDING = True

ATTR_LIST = ['sex', 'tel',
             'poscode', 'addr0', 'addr1', 'addr2', 'addr3', 'addr4',
             'birth', 'time']  # attributes of INFILE

SENSITIVE = 9
GROUP_BY_ATTR = ['time', 'tel', 'sex']  # これを元にグループ化

# 今はrandomな2進数を生成
WATER_LEN = 256
MAX_BIN = 3  # 各値につき最大の埋め込みビット

# for embedding
MODEL = '../models/model1/model_50.bin'
