#! usr/bin/env python
# -*- coding: utf-8 -*-

import subset
import anonymizer

infile = 'original_data.csv'
outfile = 'anonymized_data.csv'

attr_list = ['sex', 'tel',
             'poscode', 'addr0', 'addr1', 'addr2', 'addr3', 'addr4',
             'birth', 'time'] # attributes of infile
sensitive = 9 # sensitive attribute is not modified.
anonym = 'k-anonymity' # choose the method of anonymization
k = 3 # for k-anonymity

########### initial ############
init_row, datalist = subset.parsed_list(infile, sensitive)

########### k-anonymize ############
datalist = anonymizer.easy_anonymizer(datalist, sensitive, k, attr_list)
subset.all_sorted_list(datalist, sensitive)

########### output ############
subset.csv_composer(init_row, datalist, sensitive, outfile)
