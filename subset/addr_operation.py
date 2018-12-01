# usr/bin/ python
# coding: utf-8

import copy
from collections import OrderedDict

def formated_addr_from_addr(addr, addr2formats):
    try:
        formated_addr = addr2formats[addr]
        return formated_addr

    # KeyErrorの場合は知っているもの+知らないものにして返す
    except KeyError:
        print('KeyError: ', addr)

        extra = ''
        while True:
            extra = addr[-1] + extra
            addr = addr[:-1]
            if addr in addr2formats:
                formated_addr = copy.deepcopy(addr2formats[addr])
                for _i, _chunk in enumerate(formated_addr):
                    if _chunk == '*':
                        formated_addr[_i] = extra
                        return formated_addr

def geo_from_addr(addr, addr2geos):
    try:
        geo = addr2geos[addr]
        return geo

    # KeyErrorの場合は知っているものになるまで尻から削っていく
    except KeyError:
        print('KeyError', addr)

        while True:
            addr = addr[:-1]
            if addr in addr2geos:
                return addr2geos[addr]

def addr_range_catcher(attr_list):
    n = len(attr_list)

    try:
        first = attr_list.index('addr0')
    except:
        for i in range(n):
            if 'addr' in attr_list[i]:
                first = i
                break
    for i in range(n)[::-1]:
        if 'addr' in attr_list[i]:
            last = i
            return first, last

# "東京都渋谷区" -> {"東京都渋谷区": [135, 48], "東京都": [134, 48]}の辞書を作る
def local_addr2geos(attr_list, dataset, addr2formats, addr2geos):
    local_addr2geos = dict()

    addr_first, addr_last = addr_range_catcher(attr_list)

    addr_set = set()
    for record in dataset:
        addr_set.add(''.join(record[addr_first:addr_last+1]).strip('*'))

    hierarchical_addrs = set()
    for addr in addr_set:
        formated_addr = formated_addr_from_addr(addr, addr2formats)
        for i in range(1, len(formated_addr)+1):
            hierarchical_addrs.add(''.join(formated_addr[:i]).strip('*'))
    '''
    hierarchical_addrs = sorted(hierarchical_addrs)
    '''
    for addr in hierarchical_addrs:
        local_addr2geos[addr] = geo_from_addr(addr, addr2geos)
    local_addr2geos = OrderedDict(sorted(local_addr2geos.items(),
                                         key=lambda x: x[0]))

    return local_addr2geos

if __name__ == '__main__':
    import pickle
    import sys
    sys.path.append('../')
    from api import parsed_list

    ADDR2FORMAT_PKL = '../pickles/addr2format.pkl'
    ADDR2GEO_PKL = '../pickles/addr2geo.pkl'
    INFILE = '../anonymized_data.csv'
    ATTR_LIST = ['sex', 'tel',
                 'poscode', 'addr0', 'addr1', 'addr2', 'addr3', 'addr4',
                 'birth', 'time']  # attributes of INFILE

    with open(ADDR2FORMAT_PKL, 'rb') as f:
        addr2formats = pickle.load(f)
    with open(ADDR2GEO_PKL, 'rb') as f:
        addr2geos = pickle.load(f)

    _, dataset = parsed_list(INFILE, header=True)

    local_addr2geos = local_addr2geos(ATTR_LIST, dataset,
                                      addr2formats, addr2geos)

    for i in local_addr2geos:
        print(i, local_addr2geos[i])
