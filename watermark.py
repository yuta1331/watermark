#! usr/bin/env python
# -*- coding: utf-8 -*-

import re
import pickle
import math
# import gensim  # word2vec利用時
import subset


########## parameter ##########

EMBEDDING_VEC = '../practice/neologd.vec'

ADDR2FORMAT_PKL = 'pickles/addr2format.pkl'
ADDR2GEO_PKL = 'pickles/addr2geo.pkl'

BIT_LEN = 2

########## method ###########

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

def joined_addr(first, last, record):
    addr = ''.join(record[first:last+1])
    return re.sub(r'\*+', '', addr)

def geo_distance(geo1, geo2):
    return math.sqrt((geo1[0] - geo2[0]) ** 2 +
                     (geo1[1] - geo2[1]) ** 2)

def closest_addrs(listed_addr, num_cand, addr2formats, addr2geos, distance = False):
    # existed_addr_num: listed_addrにおける*でない値の個数
    # ['東京都', '渋谷区', '*', '*']なら2
    # closestの候補は最終的に、existed_addr_numを揃えたいが
    # 今はまだ書けていない。
    for i, _chunk in enumerate(listed_addr):
        if _chunk == '*':
            existed_addr_num = i
            break
    else:
        existed_addr_num = len(listed_addr)


    addr = ''.join(listed_addr).strip('*')
    geo = addr2geos[addr]

    closest_addrs = list()
    closest_distances = list()

    for _i, _addr in enumerate(addr2geos.keys()):
        _d = geo_distance(geo, addr2geos[_addr])

        # num_candに満たない場合はlistが溜まり切っていないので別処理
        if _i < num_cand:
            closest_addrs.append(_addr)
            closest_distances.append(_d)
            for i in range(_i):
                for j in range(1, _i + 1 - i):
                    if closest_distances[j - 1] > closest_distances[j]:
                        closest_distances[j - 1], closest_distances[j] =\
                                closest_distances[j], closest_distances[j - 1]

                        closest_addrs[j - 1], closest_addrs[j] =\
                                closest_addrs[j], closest_addrs[j - 1]

        else:
            # _ddはリスト済みの値たち
            for _ii, _dd in enumerate(closest_distances):
                if _dd > _d:
                    for i in range(_ii + 1, num_cand)[::-1]:
                        closest_distances[i] = closest_distances[i - 1]
                        closest_addrs[i] = closest_addrs[i - 1]
                    closest_distances[_ii] = _d
                    closest_addrs[_ii] = _addr
                    break

    if distance == True:
        return closest_addrs, closest_distances
    return closest_addrs




def watermarker(dataset, group_by, water_bin, attr_list, method):
    if method == 'embedding':
        model = gensim.models.KeyedVectors.load_word2vec_format(EMBEDDING_VEC,
                                                                binary=False)
        dataset = subset.sorted_list(dataset, group_by)

        # グループごとに埋め込み
        tmp_group_key = list()
        for record in dataset:
            if not water_bin:
                break

            data_key = [record[i] for i in group_by]

            # 今はグループに1つだけ編集
            # 住所のみ
            if (not tmp_group_key) or (tmp_group_key != data_key):
                tmp_group_key = data_key
                embedded_bin = water_bin[:2]
                water_bin = water_bin[2:]

                # 住所を取り出す
                addr_first, addr_last = addr_range_catcher(attr_list)
                # 住所はまとめてくっつける(*なし)
                addr = joined_addr(addr_first, addr_last, record)
                # print(embedded_bin, ' ', addr)

                # modifying
                try:
                    addr = model.most_similar(positive=[addr])\
                                            [int(embedded_bin, 2)][0]
                    print(addr)
                except:
                    water_bin = embedded_bin + water_bin

                # formatting
                # addr

                # dataset[i][addr_first:addr_last+1] = addr
        return

    elif method == 'geo':
        with open(ADDR2FORMAT_PKL, 'rb') as f:
            addr2formats = pickle.load(f)
        with open(ADDR2GEO_PKL, 'rb') as f:
            addr2geos = pickle.load(f)

        # グループごとに埋め込み
        tmp_group_key = list()
        for i_data, record in enumerate(dataset):
            if not water_bin:
                break

            data_key = [record[i] for i in group_by]

            # 今はグループに1つだけ編集
            # 住所のみ
            if (not tmp_group_key) or (tmp_group_key != data_key):
                tmp_group_key = data_key

                embedded_bin = water_bin[:BIT_LEN]
                water_bin = water_bin[BIT_LEN:]

                # 住所を取り出す
                addr_first, addr_last = addr_range_catcher(attr_list)

                # 住所はまとめてくっつける（*なし）
                addr = joined_addr(addr_first, addr_last, record)
                # print(embedded_bin, ' ', addr)

                # modifying
                try:
                    num_cand = 2**BIT_LEN
                    addr = closest_addrs(record[addr_first:addr_first+1],
                                         num_cand, addr2formats, addr2geos)\
                                         [int(embedded_bin, 2)]
                except:
                    water_bin = embedded_bin + water_bin

                # formatting
                addr = addr2formats[addr]
                addr.append('*')  # pickleのformatは'*'が1つ少ない

                dataset[i_data][addr_first:addr_last+1] = addr
                # print(dataset[i_data])
                # print(len(dataset[i_data]))
        return

def detector(origin_set, modified_set, group_by,
             attr_list, water_len, METHOD):
    detected_bin = ''

    origin_set = subset.sorted_list(origin_set, group_by)
    modified_set = subset.sorted_list(modified_set, group_by)

    # 住所のみに埋め込まれている
    addr_first, addr_last = addr_range_catcher(attr_list)

    target_group_key = list()
    target_origin_addrs = list()
    for origin_rec in origin_set:
        if water_len == 256:
            break

        # group_keyが等しいaddrを集める
        # tmpはorigin_recにおける値を指す

        tmp_origin_key = [origin_rec for i in group_by]

        if not target_group_key:
            target_group_key = tmp_origin_key
            target_origin_addrs = [origin_rec[addr_first:addr_last+1]]
            continue

        if target_group_key == tmp_origin_key:
            target_origin_addrs.append(origin_rec[addr_first:addr_last+1])
        else:
            for mod_rec in modified_set:
                tmp_mod_key = [mod_rec for i in group_by]

                if tmp_mod_key == target_group_key:
                    tmp_mod_addr = mod_rec[addr_first:addr_last+1]
                    for i, origin_addr in enumerate(target_origin_addrs):
                        if tmp_mod_addr == origin_addr:
                            del target_origin_addrs[i]
                            break
                    else: # 埋め込まれた可能性有
                        a = 0
                        # tmp_mod_addrとtarget_origin_addrs[0]との比較
                    break

            target_group_key = tmp_origin_key
            target_origin_addrs = [origin_rec[addr_first:addr_last+1]]

    return detected_bin

if __name__ == '__main__':
    with open(ADDR2FORMAT_PKL, 'rb') as f:
        addr2formats = pickle.load(f)
    with open(ADDR2GEO_PKL, 'rb') as f:
        addr2geos = pickle.load(f)
    listed_addr = ['東京都渋谷区']
    num_cand = 4

    closest_a, closest_d = closest_addrs(listed_addr, num_cand, addr2formats, addr2geos)
    for i in range(num_cand):
        print(closest_a[i], closest_d[i])
