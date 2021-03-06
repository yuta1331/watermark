#! usr/bin/env python
# -*- coding: utf-8 -*-

import pickle
import math
import copy
from collections import OrderedDict
# import gensim  # word2vec利用時

import api
from subset.addr_operation import local_addr2formatsgeos as la2fg
from subset.addr_operation import candidate_addr2geos as ca2g
from subset.addr_operation import addr_range_catcher as addr_range
from subset.addr_operation import parent_addr as pa
from subset.addr_operation import addrs_with_same_parent as asp
import consts
from Anonymizer.anonymizer import address_masking


########## parameter ##########

EMBEDDING_VEC = '../practice/neologd.vec'

ADDR2FORMAT_PKL = 'pickles/addr2format.pkl'
ADDR2GEO_PKL = 'pickles/addr2geo.pkl'

BIT_LEN = 2

MODE = consts.MODE


########## method ###########
def low_loss_watermark(water_bin, max_bin, embedded_location, datalist,
                       attr_list, group_by, addr_first, addr_last,
                       model, local_addr2formats, local_addr2geos):

    meta_dict = OrderedDict()

    # datalistをgroup化
    group_list = api.datalist2groups(datalist, group_by)

    if embedded_location is None:
        embedded_location = list(range(len(group_list)))

    for group_i in embedded_location:
        group = group_list[group_i]  # 参照渡し
        i2b_dict = OrderedDict()

        # print('######## group_i: ', group_i, '########')

        # append index and parent
        for index, record in enumerate(group):  # recordは参照渡し
            record.append(index)
            parent = pa(record[addr_first:addr_last+1])
            record.append(parent)

        # parentでグループ分け
        # 追加時にparentはpopしちゃう
        group_by_parent = OrderedDict()
        for record in group:
            if record[-1] in group_by_parent.keys():
                # recordは参照渡し
                group_by_parent[record.pop()].append(record)
            else:
                # recordは参照渡し
                group_by_parent[record.pop()] = [record]

        for parent_group in group_by_parent.values():
            # parent_groupは参照渡し

            for record in parent_group:  # 参照渡し

                # indexがpopされているということ
                if len(record) == len(attr_list):
                    break

                formatted_addr = record[addr_first:addr_last+1]
                addr = ''.join(formatted_addr).strip('*')

                candidate_addresses = ca2g(
                    formatted_addr,
                    local_addr2formats,
                    local_addr2geos,
                    model
                    )

                if candidate_addresses is not None:
                    embed_num = min(
                        max_bin,
                        int(math.log2(len(candidate_addresses)))
                        )

                    if len(water_bin) > 0:
                        # print('######## i in group: ',
                        #       record[-1],
                        #       '########')

                        embed_num = min(embed_num, len(water_bin))

                        embed_bin = water_bin[:embed_num]
                        water_bin = water_bin[embed_num:]

                        embedded_addr = candidate_addresses[
                            int(embed_bin, 2)
                            ]

                        # print('embe: ', embed_bin)
                        # print('prev: ', addr)
                        # print('modi: ', embedded_addr)
                        # formatting
                        embedded_addr = copy.deepcopy(
                            local_addr2formats[embedded_addr]
                            )
                        # pickleのformatは'*'が1つ少ない
                        embedded_addr.append('*')
                        # print('\n')

                        # modifying
                        record[addr_first:addr_last+1] = embedded_addr

                        i2b_dict[record[-1]] = embed_num
                        for tmp_record in parent_group:
                            del tmp_record[-1]

                    # water_bin has been run out
                    else:
                        for record in datalist:
                            del record[len(attr_list):]
                        api.groups2datalist(datalist, group_list)

                        # {group_i: {_i: embed_num}}
                        if i2b_dict:
                            meta_dict[group_i] = i2b_dict
                        return meta_dict

        # {group_i: {_i: embed_num}}
        if i2b_dict:
            meta_dict[group_i] = i2b_dict


def more_loss_watermarker(water_bin, embedded_location, datalist,
                          attr_list, group_by, addr_first, addr_last):

    meta_dict = OrderedDict()

    # datalistをgroup化
    group_list = api.datalist2groups(datalist, group_by)

    if embedded_location is None:
        embedded_location = list(range(len(group_list)))

    for group_i in embedded_location:
        group = group_list[group_i]  # 参照渡し

        # print('######## group_i: ', group_i, '########')

        if len(water_bin) > 0:

            embed_num = min(int(math.log2(len(group)+1)),
                                 len(water_bin))

            embed_bin = water_bin[:embed_num]
            water_bin = water_bin[embed_num:]

            # print('###### embe: ', embed_bin, ' ######')

            for i in range(int(embed_bin, 2)):
                addr = group[i][addr_first:addr_last+1]
                # print('prev: ', addr)
                mod_addr = address_masking(attr_list[addr_first:addr_last+1],
                                           addr)
                # print('modi: ', mod_addr)
                for mod_i, addr_i in enumerate(range(addr_first, addr_last+1)):
                    group[i][addr_i] = mod_addr[mod_i]

            meta_dict[group_i] = embed_num

        else:
            return meta_dict


def watermarker(datalist, water_bin, max_bin, embedded_location,
                attr_list, group_by, method, model):

    if method == 'geo':
        # print('Watermarking with GeoLocation')
        addr_first, addr_last = addr_range(attr_list)
        with open(ADDR2FORMAT_PKL, 'rb') as f:
            addr2formats = pickle.load(f)
        with open(ADDR2GEO_PKL, 'rb') as f:
            addr2geos = pickle.load(f)

        # localized dictionaries
        local_addr2formats, local_addr2geos =\
            la2fg(attr_list, datalist, addr2formats, addr2geos)

        if MODE == 'proposal':
            # 埋め込み位置と何ビット埋め込んだか保存
            # meta_dict = {group_i: i2b_dict}
            # i2b_dict = {_i: embed_num}
            meta_dict = low_loss_watermark(
                    water_bin, max_bin, embedded_location, datalist,
                    attr_list, group_by, addr_first, addr_last,
                    model, local_addr2formats, local_addr2geos
                    )
        elif MODE == 'existing':
            # meta_dict = [group_i]
            meta_dict = more_loss_watermarker(
                    water_bin, embedded_location, datalist,
                    attr_list, group_by, addr_first, addr_last
                    )

        return meta_dict


def same_group_as_org_g(org_g, mod_group_l, group_by):
    for mod_g in mod_group_l:
        for i in group_by:
            if org_g[0][i] != mod_g[0][i]:
                break
        else:
            # group_byの値が全て同じ場合
            return mod_g
    else:
        # 全部breakされて引っかからなかった場合
        return None


def low_loss_detector(group_i, org_g, mod_g, extract_num,
                      extracted_bin, meta_dict, addr_first, addr_last,
                      model, local_addr2formats, local_addr2geos):
    if mod_g is None:
        # print('Error: the same group is not found')
        # print('       group_i: ', group_i)
        # print('       group  : ', org_g)
        for embed_num in meta_dict[group_i].values():
            extracted_bin += format(
                    0,
                    '0>' + str(embed_num) + 'b'
                    )
            extract_num += embed_num
        return extract_num, extracted_bin

    for _i in meta_dict[group_i].keys():
        formatted_org_addr = org_g[_i][addr_first:addr_last+1]
        org_addr = ''.join(formatted_org_addr).strip('*')
        org_parent_addr = pa(formatted_org_addr)

        # parent_addrが同じaddrをorg_gから取ってくる
        # formatでなく連結でOK
        org_addrs_with_same_parent = asp(
                org_parent_addr, org_g,
                addr_first, addr_last
                )

        # parent_addrが同じaddrをmod_gから取ってくる
        # formatでなく連結でOK
        mod_addrs_with_same_parent = asp(
                org_parent_addr, mod_g,
                addr_first, addr_last
                )

        # 上二つから同一の値を削除していき、差分を発見する
        org_addrs_with_same_parent.remove(org_addr)
        tmp_org_addrs = copy.deepcopy(org_addrs_with_same_parent)
        for tmp_org_addr in tmp_org_addrs:
            if tmp_org_addr in mod_addrs_with_same_parent:
                org_addrs_with_same_parent.remove(tmp_org_addr)
                mod_addrs_with_same_parent.remove(tmp_org_addr)

        if len(mod_addrs_with_same_parent) > 0:
            # org_addrとmod_addrs_with_same_parent[0]から
            # 埋め込みビットを抽出
            # org_addrの編集候補を並べる
            # mod_addrs_with_same_parent[0]がそのどれに当たるか
            candidate_addresses = ca2g(
                formatted_org_addr,
                local_addr2formats,
                local_addr2geos,
                model
                )

            candidate_mod_addr = mod_addrs_with_same_parent[0]
            # print('######## i in dgroup: ', _i, ' ########')
            if candidate_mod_addr in candidate_addresses:
                embed_num = meta_dict[group_i][_i]
                extracted_chunk = candidate_addresses.\
                    index(candidate_mod_addr)
                extracted_chunk = format(
                    extracted_chunk,
                    '0>' + str(embed_num) + 'b'
                    )
                if embed_num < len(extracted_chunk):
                    extracted_chunk = extracted_chunk[:embed_num]
                # print('embe: ', extracted_chunk)
                # print('prev: ', org_addr)
                # print('modi: ', mod_addrs_with_same_parent)
                # print('\n')
                extracted_bin += extracted_chunk
                extract_num += meta_dict[group_i][_i]
        else:
            extracted_bin += format(
                0,
                '0>' + str(meta_dict[group_i][_i]) + 'b'
                )
            extract_num += meta_dict[group_i][_i]

    return extract_num, extracted_bin


def more_loss_detector(group_i, org_g, mod_g, extract_num, water_len,
                       attr_list, extracted_bin, addr_first, addr_last):
    embed_num = min(int(math.log2(len(org_g)+1)),
                    water_len - len(extracted_bin))
    # print('{:3}'.format(group_i), embed_num)
    if mod_g is None:
        # print('Error: the same group is not found')
        # print('       group_i: ', group_i)
        # print('       group  : ', org_g)
        extracted_bin += format(
                0,
                '0>' + str(embed_num) + 'b'
                )
        extract_num += embed_num
        return extract_num, extracted_bin

    # clipping addrs
    org_addr_g = [x[addr_first:addr_last+1] for x in org_g]
    mod_addr_g = [x[addr_first:addr_last+1] for x in mod_g]

    # sorting org_addr_g
    sortKey = lambda x: x.index('*')
    org_addr_g.sort(key=sortKey)

    for i, org_addr in reversed(list(enumerate(org_addr_g))):
        if org_addr in mod_addr_g:
            del org_addr_g[i]
            mod_addr_g.remove(org_addr)
        else:
            masked_addr = address_masking(attr_list[addr_first:addr_last+1],
                                          org_addr)
            if masked_addr in mod_addr_g:
                mod_addr_g.remove(masked_addr)

    extracted_chunk = ('{:0='+str(embed_num)+'b}').format(len(org_addr_g))
    extracted_bin += extracted_chunk
    extract_num += len(extracted_chunk)
    return extract_num, extracted_bin


def detector(org_l, mod_l, max_bin, meta_dict, attr_list,
             group_by, water_len, method, model):

    extracted_bin = ''
    extract_num = 0

    # datalistをgroup化
    org_group_l = api.datalist2groups(org_l, group_by)
    mod_group_l = api.datalist2groups(mod_l, group_by)

    # 住所のみに埋め込まれている
    addr_first, addr_last = addr_range(attr_list)

    if method == 'geo':
        with open(ADDR2FORMAT_PKL, 'rb') as f:
            addr2formats = pickle.load(f)
        with open(ADDR2GEO_PKL, 'rb') as f:
            addr2geos = pickle.load(f)

        # localized dictionaries
        local_addr2formats, local_addr2geos =\
            la2fg(attr_list, org_l, addr2formats, addr2geos)

        # 埋め込まれたグループのみ
        for group_i in meta_dict.keys():
            # print('######## dgroup_i: ', group_i, ' ########')
            org_g = org_group_l[group_i]

            # org_gとgroup_byの値が同じグループをmod_gから取り出す
            mod_g = same_group_as_org_g(org_g, mod_group_l, group_by)
            if MODE == 'proposal':
                extract_num, extracted_bin = low_loss_detector(
                        group_i, org_g, mod_g, extract_num, extracted_bin,
                        meta_dict, addr_first, addr_last,
                        model, local_addr2formats, local_addr2geos
                        )
            elif MODE == 'existing':
                extract_num, extracted_bin = more_loss_detector(
                        group_i, org_g, mod_g, extract_num, water_len,
                        attr_list, extracted_bin, addr_first, addr_last
                        )

    # print('extract num: ', extract_num)
    return extracted_bin
