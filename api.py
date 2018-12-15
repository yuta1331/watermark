#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv


def sorted_list(datalist, priority, ignored_list=[]):
    if priority is None:
        priority = list(range(len(datalist[0])))
    for i in priority[::-1]:
        if i not in ignored_list:
            datalist.sort(key=lambda x: x[i])
    return datalist


# priorityの属性が等しいレコード同士でグループ化する
def datalist2groups(datalist, priority):
    datalist = sorted_list(datalist, priority)
    groups = list()
    _tmp_group = [datalist[0]]
    for record in datalist[1:]:
        for _prio in priority:
            if record[_prio] != _tmp_group[0][_prio]:
                groups.append(_tmp_group)
                _tmp_group = [record]
                break
        else:
            _tmp_group.append(record)
    groups.append(_tmp_group)
    return groups


def groups2datalist(datalist, groups):
    i = 0
    for group in groups:
        for record in group:
            datalist[i] = record
            i += 1
    return


############ API ##############
def parsed_list(infile, header=False):
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

    if header:
        csv_header = datalist[0]
        datalist = datalist[1:]
        return csv_header, datalist
    return datalist


def csv_composer(init_row, outlist, outfile):
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
    _, datalist = parsed_list('csvs/anonymized_data.csv', header=True)
    group_list = datalist2groups(datalist, group_by)

    for equal in group_list:
        print(equal)
        print('\n')
