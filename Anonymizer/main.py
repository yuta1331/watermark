#! usr/bin/env python
# -*- coding: utf-8 -*-

import subset
import anonymizer

INFILE = 'original_data.csv'
OUTFILE = 'anonymized_data.csv'

ATTR_LIST = ['sex', 'tel',
             'poscode', 'addr0', 'addr1', 'addr2', 'addr3', 'addr4',
             'birth', 'time']  # attributes of INFILE
SENSITIVE = 9  # sensitive attribute is not modified.
ANONYM = 'k-anonymity'  # choose the method of anonymization
K = 4  # for k-anonymity
ATTR_PRIORITY = ['sex', 'addr0', 'addr1', 'addr2', 'addr3', 'addr4',
                 'poscode', 'tel', 'birth', 'time']

########### initial ############
init_row, datalist = subset.parsed_list(INFILE, SENSITIVE)
priority = [ATTR_LIST.index(attr) for attr in ATTR_PRIORITY]


########### k-anonymize ############
datalist = anonymizer.easy_anonymizer(datalist,
                                      SENSITIVE,
                                      K,
                                      ATTR_LIST,
                                      priority)
subset.all_sorted_list(datalist, SENSITIVE, None)

freq = anonymizer.freq_list(datalist, SENSITIVE)
calc_k = anonymizer.calc_k(freq)
print(ANONYM, ': ', calc_k)


########### output ############
subset.csv_composer(init_row, datalist, SENSITIVE, OUTFILE)
