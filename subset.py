#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv

def all_sorted_list(datalist, sensitive):
    for i in range(len(datalist[0]))[::-1]:
        if i != sensitive:
            datalist.sort(key=lambda x:x[i])
    return datalist



############ API ##############
def parsed_list(infile, sensitive):
    try:
        datalist = list()
        with open(infile, 'r') as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=',')
            for row in csv_reader:
                # row = ['女', '040417329', '299-0225', '千葉県', '袖ケ浦市',
                #        '玉野', '1-15-4', '', '1991/11/02', '158']
                datalist.append(row)
    except FileNotFoundError as e:
        print(e)
    except csv.Error as e:
        print(e)
    init = datalist[0]
    datalist = datalist[1:]
    return init, all_sorted_list(datalist, sensitive)

def csv_composer(init_row, outlist, sensitive, outfile):
    outlist = all_sorted_list(outlist, sensitive)
    try:
        with open(outfile, 'w') as csvfile:
            writer = csv.writer(csvfile, lineterminator='\n')
            for row in [init_row] + outlist:
                writer.writerow(row)
    except FileNotFoundError as e:
        print(e)
    except csv.Error as e:
        print(e)
