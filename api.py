#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv

def sorted_list(dataset, priority):
    if priority == None:
        priority = list(range(len(dataset[0])))
    for i in priority[::-1]:
        dataset.sort(key=lambda x:x[i])
    return dataset



############ API ##############
def parsed_list(infile, header=False):
    try:
        dataset = list()
        with open(infile, 'r') as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=',')
            for row in csv_reader:
                # row = ['女', '040417329', '299-0225', '千葉県', '袖ケ浦市',
                #        '玉野', '1-15-4', '', '1991/11/02', '158']
                dataset.append(row)
    except FileNotFoundError as e:
        print(e)
    except csv.Error as e:
        print(e)

    if header:
        csv_header = dataset[0]
        dataset = dataset[1:]
        return csv_header, dataset
    return dataset

def csv_composer(init_row, outlist, outfile):
    # outlist = sorted_list(outlist, None)
    try:
        with open(outfile, 'w') as csvfile:
            writer = csv.writer(csvfile, lineterminator='\n')
            for row in [init_row] + outlist:
                writer.writerow(row)
    except FileNotFoundError as e:
        print(e)
    except csv.Error as e:
        print(e)
