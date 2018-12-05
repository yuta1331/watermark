#! usr/bin/env python
# -*- coding: utf-8 -*-

import pickle
import math
import copy
# import gensim  # word2vec利用時

import api
from subset.addr_operation import local_addr2formatsgeos as la2fg
from subset.addr_operation import candidate_addr2geos as caddr2geos
from subset.addr_operation import addr_range_catcher as addr_range


########## parameter ##########

EMBEDDING_VEC = '../practice/neologd.vec'

ADDR2FORMAT_PKL = 'pickles/addr2format.pkl'
ADDR2GEO_PKL = 'pickles/addr2geo.pkl'

BIT_LEN = 2

########## method ###########

def watermarker(datalist, water_bin, max_bin, embedded_location,
                attr_list, group_by, method):

    # 埋め込み位置と何ビット埋め込んだか保存
    # [group_i, _i, embed_num]
    water_locate_n_num = list()

    # datalistをgroup化
    group_list = api.datalist2groups(datalist, group_by)

    if embedded_location == None:
        embedded_location = list(range(len(group_list)))

    if method == 'geo':
        print('Watermarking with GeoLocation')
        addr_first, addr_last = addr_range(attr_list)
        with open(ADDR2FORMAT_PKL, 'rb') as f:
            addr2formats = pickle.load(f)
        with open(ADDR2GEO_PKL, 'rb') as f:
            addr2geos = pickle.load(f)

        # localized dictionaries
        local_addr2formats, local_addr2geos =\
            la2fg(attr_list, datalist, addr2formats, addr2geos)

        for group_i in embedded_location:
            group = group_list[group_i] # 参照渡し

            print('######## group_i: ', group_i, '########')

            prev_addr = ''
            for _i, record in enumerate(group):
                formated_addr = record[addr_first:addr_last+1]
                addr = ''.join(formated_addr).strip('*')

                if prev_addr != addr:
                    prev_addr = addr
                    candidate_addresses = caddr2geos(
                        formated_addr,
                        local_addr2formats,
                        local_addr2geos
                        )

                    if candidate_addresses != None:
                        embed_num = min(
                            max_bin,
                            int(math.log2(len(candidate_addresses)))
                            )

                        if len(water_bin) > 0:
                            print('######## i in group: ', _i, '########')
                            embed_bin = water_bin[:embed_num]
                            water_bin = water_bin[embed_num:]

                            embedded_addr = candidate_addresses[
                                int(embed_bin, 2)
                                ]

                            print('embe: ', embed_bin)
                            print('prev: ', addr)
                            print('modi: ', embedded_addr)
                            # formatting
                            embedded_addr = copy.deepcopy(
                                addr2formats[embedded_addr]
                                )
                            embedded_addr.append('*')  # pickleのformatは'*'が1つ少ない
                            print('modn: ', len(embedded_addr))
                            print('\n')

                            # modifying
                            group_list[group_i][_i]\
                                [addr_first:addr_last+1]\
                                = embedded_addr

                            water_locate_n_num.append([group_i, 
                                                      _i,
                                                      embed_num])
                        # water_bin has been run out
                        else:
                            api.groups2datalist(datalist, group_list)
                            return water_locate_n_num


def detector(org_l, mod_l, max_bin, water_locate_n_num,
             attr_list, group_by, water_len, method):
    detected_bin = ''

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

        for group_i in range(len(org_group_l)):
            org_g = org_group_l[group_i]
            mod_g = mod_group_l[group_i]

            for _i in range(len(org_g)):
                org_addr = org_g[_i][addr_first:addr_last+1]
                org_addr = ''.join(org_addr).strip('*')

                mod_addr = mod_g[_i][addr_first:addr_last+1]
                mod_addr = ''.join(mod_addr).strip('*')




        for i_data, org_record in enumerate(org_l):
            if len(detected_bin) == 256:
                break

            # 住所はまとめてくっつける（*なし）
            org_addr = joined_addr(addr_first, addr_last, org_record)
            mod_addr = joined_addr(addr_first, addr_last, mod_l[i_data])

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
