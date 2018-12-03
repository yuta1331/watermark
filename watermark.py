#! usr/bin/env python
# -*- coding: utf-8 -*-

import pickle
# import gensim  # word2vec利用時

import api
from subset.addr_operation import local_addr2formatsgeos as la2fg
from subset.addr_operation import candidate_addresses as caddr
from subset.addr_operation import geo_distance
from subset.addr_operation import addr_range_catcher as addr_range


########## parameter ##########

EMBEDDING_VEC = '../practice/neologd.vec'

ADDR2FORMAT_PKL = 'pickles/addr2format.pkl'
ADDR2GEO_PKL = 'pickles/addr2geo.pkl'

BIT_LEN = 2

########## method ###########

def nearest_addrs(listed_addr, num_cand, addr2formats, addr2geos, distance = False):
    # existed_addr_num: listed_addrにおける*でない値の個数
    # ['東京都', '渋谷区', '*', '*']なら2
    # nearestの候補は最終的に、existed_addr_numを揃えたいが
    # 今はまだ書けていない。
    for i, _chunk in enumerate(listed_addr):
        if _chunk == '*':
            existed_addr_num = i
            break
    else:
        existed_addr_num = len(listed_addr)


    addr = ''.join(listed_addr).strip('*')
    geo = addr2geos[addr]

    nearest_addrs = list()
    nearest_distances = list()

    for _i, _addr in enumerate(addr2geos.keys()):
        _d = geo_distance(geo, addr2geos[_addr])

        # num_candに満たない場合はlistが溜まり切っていないので別処理
        if _i < num_cand:
            nearest_addrs.append(_addr)
            nearest_distances.append(_d)
            for i in range(_i):
                for j in range(1, _i + 1 - i):
                    if nearest_distances[j - 1] > nearest_distances[j]:
                        nearest_distances[j - 1], nearest_distances[j] =\
                                nearest_distances[j], nearest_distances[j - 1]

                        nearest_addrs[j - 1], nearest_addrs[j] =\
                                nearest_addrs[j], nearest_addrs[j - 1]

        else:
            # _ddはリスト済みの値たち
            for _ii, _dd in enumerate(nearest_distances):
                if _dd > _d:
                    for i in range(_ii + 1, num_cand)[::-1]:
                        nearest_distances[i] = nearest_distances[i - 1]
                        nearest_addrs[i] = nearest_addrs[i - 1]
                    nearest_distances[_ii] = _d
                    nearest_addrs[_ii] = _addr
                    break

    if distance == True:
        return nearest_addrs, nearest_distances
    return nearest_addrs




def watermarker(datalist, water_bin, max_bin, embedded_location,
                attr_list, group_by, method):

    # datalistをgroup化
    group_list = api.equal_list(datalist, group_by)
    print(type(group_list))

    if embedded_location == None:
        embedded_location = list(range(len(group_list)))

    if method == 'geo':
        print('Watermarking with GeoLocation')
        addr_first, addr_last = addr_range(attr_list)
        with open(ADDR2FORMAT_PKL, 'rb') as f:
            addr2formats = pickle.load(f)
        with open(ADDR2GEO_PKL, 'rb') as f:
            addr2geos = pickle.load(f)

        for group_i in embedded_location:
            group = group_list[group_i] # 参照渡し？
            print('group:\n', group)

            local_addr2formats, local_addr2geos =\
                la2fg(attr_list, datalist, addr2formats, addr2geos)

            formated_addr = group[addr_first:]
            candidate_addresses = caddr(formated_addr,
                                        local_addr2formats,
                                        local_addr2geos)


def detector(org_list, mod_list, group_by,
             attr_list, water_len, method):
    detected_bin = ''

    org_list = api.sorted_list(org_list, group_by)
    mod_list = api.sorted_list(mod_list, group_by)

    # 住所のみに埋め込まれている
    addr_first, addr_last = addr_range_catcher(attr_list)


    if method == 'geo':
        with open(ADDR2FORMAT_PKL, 'rb') as f:
            addr2formats = pickle.load(f)
        with open(ADDR2GEO_PKL, 'rb') as f:
            addr2geos = pickle.load(f)

        num_changed = 0  # for debug

        for i_data, org_record in enumerate(org_list):
            if len(detected_bin) == 256:
                break

            # 住所はまとめてくっつける（*なし）
            org_addr = joined_addr(addr_first, addr_last, org_record)
            mod_addr = joined_addr(addr_first, addr_last, mod_list[i_data])

            num_cand = 2**BIT_LEN
            if org_addr != mod_addr:
                num_changed += 1

                # 付け焼刃で[1:]
                nearest_addresses = nearest_addrs(org_record[addr_first:addr_last+1],
                                                  num_cand+1,
                                                  addr2formats,
                                                  addr2geos)[1:]

                rank = 0
                for i, cand_address in enumerate(nearest_addresses):
                    if cand_address == mod_addr:
                        rank = i
                        break

                detected_bin += format(rank, 'b').zfill(BIT_LEN)
        print(num_changed)


    '''
    # 一旦待った
    target_group_key = list()
    target_org_addrs = list()
    for org_record in org_list:
        if len(detected_bin) == 256:
            break

        # group_keyが等しいaddrを集める
        # tmpはorg_recordにおける値を指す
        # record

        tmp_org_key = [org_record for i in group_by]

        if not target_group_key:
            target_group_key = tmp_org_key
            target_org_addrs = [org_record[addr_first:addr_last+1]]
            continue

        if target_group_key == tmp_org_key:
            target_org_addrs.append(org_record[addr_first:addr_last+1])
        else:
            for mod_record in mod_list:
                tmp_mod_key = [mod_record for i in group_by]

                if tmp_mod_key == target_group_key:
                    tmp_mod_addr = mod_record[addr_first:addr_last+1]
                    for i, org_addr in enumerate(target_org_addrs):
                        if tmp_mod_addr == org_addr:
                            del target_org_addrs[i]
                            break
                    else: # 埋め込まれた可能性有
                        # tmp_mod_addrとtarget_org_addrs[0]との比較
                    break

            target_group_key = tmp_org_key
            target_org_addrs = [org_record[addr_first:addr_last+1]]
    '''

    return detected_bin

if __name__ == '__main__':
    '''
    with open(ADDR2FORMAT_PKL, 'rb') as f:
        addr2formats = pickle.load(f)
    with open(ADDR2GEO_PKL, 'rb') as f:
        addr2geos = pickle.load(f)
    listed_addr = ['東京都渋谷区']
    num_cand = 4

    nearest_a, nearest_d = nearest_addrs(listed_addr, num_cand, addr2formats, addr2geos, distance=True)
    for i in range(num_cand):
        print(nearest_a[i], nearest_d[i])
    '''
