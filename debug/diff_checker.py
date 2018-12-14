#! usr/bin/env python
# -*- coding: utf-8 -*-

# 透かし前後で変わったデータの数を数える

import sys
sys.path.append('../')
import api

INFILE = '../csvs/anonymized_data.csv'
OUTFILE = '../csvs/watermarked_data.csv'

csv_header, org_set = api.parsed_list(INFILE, True)
_, mod_set = api.parsed_list(OUTFILE, True)

not_match_num = 0
for i, org in enumerate(org_set):
    if org != mod_set[i]:
        not_match_num += 1

print(not_match_num)
