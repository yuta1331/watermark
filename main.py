#!/usr/bin/env python

import subset
import anonymizer

infile = 'original_data.csv'
outfile = 'anonymized_data.csv'

attr_list = ['sex', 'tel',
             ['poscode', 'add0', 'add1', 'add2', 'add3', 'add4'],
             'birth', 'time'] # attributes of infile
sensitive = 9 # sensitive attribute is not modified.
anonym = 'k-anonymity' # choose the method of anonymization
k = 3 # for k-anonymity

########### initial ############
init_row, datalist = subset.parsed_list(infile, sensitive)

########### k-anonymity ############


########### output ############
subset.csv_composer(init_row, datalist, sensitive, outfile)
