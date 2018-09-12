#! usr/bin/env python
# -*- coding: utf-8 -*-

import subset
import watermark

infile = '../Anonymizer/anonymized_data.csv'
outfile = 'watermarked_data.csv'

attr_list = ['sex', 'tel',
             'poscode', 'addr0', 'addr1', 'addr2', 'addr3', 'addr4',
             'birth', 'time'] # attributes of infile

sensitive = 9

########### initial ############
init_row, datalist = subset.parsed_list(infile, sensitive)

########### watermark ############

########### output ############
subset.csv_composer(init_row, datalist, sensitive, outfile)
