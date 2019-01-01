# usr/bin/ python
# coding: utf-8

import re
import math
import copy
from collections import OrderedDict

from . import embedding_operation
import sys
sys.path.append('../')
import consts


def joined_addr(first, last, record):
    addr = ''.join(record[first:last+1])
    return re.sub(r'\*+', '', addr)


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


def parent_addr(formatted_addr):
    if '*' in formatted_addr:
        if formatted_addr.index('*') == 1:
            return None
        return ''.join(formatted_addr[:formatted_addr.index('*')-1])
    else:
        return ''.join(formatted_addr[:-1])


def addrs_with_same_parent(parent_addr_, group, addr_first, addr_last):
    result = list()
    for _record in group:
        _formatted_addr = _record[addr_first:addr_last+1]
        _parent_addr = parent_addr(_formatted_addr)
        if _parent_addr == parent_addr_:
            result.append(''.join(_formatted_addr).strip('*'))
    return result


################ dictionaries ##################

def formatted_addr_from_addr(addr, addr2formats):
    try:
        formatted_addr = addr2formats[addr]
        return formatted_addr

    # KeyErrorの場合は知っているもの+知らないものにして返す
    except KeyError:
        # print('KeyError: ', addr)

        extra = ''
        while True:
            extra = addr[-1] + extra
            addr = addr[:-1]
            if addr in addr2formats:
                formatted_addr = copy.deepcopy(addr2formats[addr])
                for _i, _chunk in enumerate(formatted_addr):
                    if _chunk == '*':
                        formatted_addr[_i] = extra
                        return formatted_addr


def geo_from_addr(addr, addr2geos):
    try:
        geo = addr2geos[addr]
        return geo

    # KeyErrorの場合は知っているものになるまで尻から削っていく
    except KeyError:
        # print('KeyError: ', addr)

        while True:
            addr = addr[:-1]
            if addr in addr2geos:
                return addr2geos[addr]


# "東京都渋谷区" -> {"東京都渋谷区": [135, 48], "東京都": [134, 48]}の辞書を作る
def local_addr2formatsgeos(attr_list, datalist, addr2formats, addr2geos):
    addr_first, addr_last = addr_range_catcher(attr_list)

    addr_set = set()
    for record in datalist:
        addr_set.add(''.join(record[addr_first:addr_last+1]).strip('*'))

    hierarchical_addrs = set()
    for addr in addr_set:
        formatted_addr = formatted_addr_from_addr(addr, addr2formats)
        for i in range(1, len(formatted_addr)+1):
            hierarchical_addrs.add(''.join(formatted_addr[:i]).strip('*'))
    '''
    hierarchical_addrs = sorted(hierarchical_addrs)
    '''

    local_addr2formats = dict()
    local_addr2geos = dict()

    for addr in hierarchical_addrs:
        local_addr2formats[addr] = formatted_addr_from_addr(addr, addr2formats)
        local_addr2geos[addr] = geo_from_addr(addr, addr2geos)

    local_addr2formats = OrderedDict(sorted(local_addr2formats.items(),
                                            key=lambda x: x[0]))
    local_addr2geos = OrderedDict(sorted(local_addr2geos.items(),
                                         key=lambda x: x[0]))

    return local_addr2formats, local_addr2geos


################ geo calculators ##################
def geo_distance(geo1, geo2):
    return math.sqrt((geo1[0] - geo2[0]) ** 2 +
                     (geo1[1] - geo2[1]) ** 2)


def candidate_addresses(formatted_addr, addr2formats):
    # 候補がなければNoneを返す

    if formatted_addr[1] == '*':
        return None
    else:
        cand_addrs = set()

        # 自分自身
        cand_addrs.add(''.join(formatted_addr).strip('*'))

        # 一個上の階層
        parent = parent_addr(formatted_addr)
        # cand_addrs.add(''.join(parent).strip('*'))

        # 自分と同じ親を持つ同階層の値
        for _addr in addr2formats.values():
            _parent = parent_addr(_addr)
            if _parent == parent:
                cand_addrs.add(''.join(_addr).strip('*'))
        return cand_addrs


def candidate_addr2geos(formatted_addr, addr2formats,
                        addr2geos, model=None, distance=False):
    # 候補がなければNoneを返す

    cand_addrs = candidate_addresses(formatted_addr, addr2formats)
    if cand_addrs is None:
        return None

    if len(cand_addrs) == 1:
        return None

    addr = ''.join(formatted_addr).strip('*')

    cand_addr2geos = dict()

    if consts.IS_EMBEDDING:
        addr_vec = model.get_word_vector(addr)

        for cand_addr in cand_addrs:
            cand_addr_vec = model.get_word_vector(cand_addr)
            cand_addr2geos[cand_addr] = embedding_operation\
                                        .cosine_similarity(addr_vec,
                                                           cand_addr_vec)

    else:
        geo = addr2geos[addr]

        for cand_addr in cand_addrs:
            cand_addr2geos[cand_addr] = geo_distance(geo, addr2geos[cand_addr])

    cand_addr2geos = OrderedDict(sorted(cand_addr2geos.items(),
                                        key=lambda x: x[1],
                                        reverse=consts.IS_EMBEDDING))

    cand_addr2geos.move_to_end(addr, False)

    if distance is True:
        return cand_addr2geos
    else:
        return list(cand_addr2geos.keys())


if __name__ == '__main__':
    import pickle
    import sys
    sys.path.append('../')
    from api import parsed_list

    ADDR2FORMAT_PKL = '../pickles/addr2format.pkl'
    ADDR2GEO_PKL = '../pickles/addr2geo.pkl'
    INFILE = '../csvs/anonymized_data.csv'
    ATTR_LIST = ['sex', 'tel',
                 'poscode', 'addr0', 'addr1', 'addr2', 'addr3', 'addr4',
                 'birth', 'time']  # attributes of INFILE

    # pickle read
    with open(ADDR2FORMAT_PKL, 'rb') as f:
        addr2formats = pickle.load(f)
    with open(ADDR2GEO_PKL, 'rb') as f:
        addr2geos = pickle.load(f)

    # csv parser
    _, datalist = parsed_list(INFILE, header=True)

    local_addr2formats, local_addr2geos =\
        local_addr2formatsgeos(ATTR_LIST, datalist, addr2formats, addr2geos)

    # candidate: nearest addrs and their distances
    addr_first, addr_last = addr_range_catcher(ATTR_LIST)
    '''
    for record in datalist:
        print(
            candidate_addr2geos(record[addr_first:addr_last+1],
                                local_addr2formats,
                                local_addr2geos, True)
        )
    '''

    '''
    # local_addr2geos
    for i in local_addr2geos:
        print(i, local_addr2formats[i])
    '''
    # print('######## parent ########')
    for record in datalist:
        addr = record[addr_first:addr_last+1]
        parent = parent_addr(addr)
        # print('origin: ', addr)
        # print('parent: ', parent)
