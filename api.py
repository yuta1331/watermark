#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv

def sorted_list(dataset, priority):
    if priority == None:
        priority = list(range(len(dataset[0])))
    for i in priority[::-1]:
        dataset.sort(key=lambda x:x[i])
    return dataset

def equal_set(dataset, priority):
    dataset = sorted_list(dataset, priority)
    groups = list()
    _tmp_group = [dataset.pop(0)]
    for record in dataset:
        for _prio in priority:
            if record[_prio] != _tmp_group[0][_prio]:
                groups.append(_tmp_group)
                _tmp_group = [record]
                break
        else:
            _tmp_group.append(record)
    groups.append(_tmp_group)
    return groups


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


if __name__ == '__main__':
    ATTR_LIST = ['sex', 'tel',
                 'poscode', 'addr0', 'addr1', 'addr2', 'addr3', 'addr4',
                 'birth', 'time']  # attributes of INFILE
    GROUP_BY_ATTR = ['time', 'tel', 'sex']  # これを元にグループ化
    group_by = [ATTR_LIST.index(attr) for attr in GROUP_BY_ATTR]
    _, dataset = parsed_list('anonymized_data.csv', header=True)
    group_set = equal_set(dataset, group_by)

    for equal in group_set:
        print(equal)
        print('\n')
