#! usr/bin/env python
# -*- coding: utf-8 -*-

import subset
import watermark

import collections

infile = '../Anonymizer/anonymized_data.csv'
outfile = 'watermarked_data.csv'

attr_list = ['sex', 'tel',
             'poscode', 'addr0', 'addr1', 'addr2', 'addr3', 'addr4',
             'birth', 'time'] # attributes of infile

sensitive = 9
group_by_attr = ['time']

########### initial ############
init_row, datalist = subset.parsed_list(infile)
group_by = [attr_list.index(attr) for attr in group_by_attr]

########### watermark ############
datalist = subset.sorted_list(datalist, group_by)

attr = [data[9] for data in datalist]
c = collections.Counter(attr)
print('minimum group: ', min(c.values()))

########### output ############
subset.csv_composer(init_row, datalist, outfile)
