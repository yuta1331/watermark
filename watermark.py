#! usr/bin/env python
# -*- coding: utf-8 -*-

import re
import gensim # word2vec利用時

import subset

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

def watermarker(dataset, group_by, water_bin, attr_list, embedding_vec):
    model = gensim.models.KeyedVectors.load_word2vec_format(embedding_vec,
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
            embeded_bin = water_bin[:2]
            water_bin = water_bin[2:]

            # 住所を取り出す
            addr_first, addr_last = addr_range_catcher(attr_list)
            # 住所はまとめてくっつける(*なし)
            addr = joined_addr(addr_first, addr_last, record)
            # print(embeded_bin, ' ', addr)

            # modifying
            try:
                addr = model.most_similar(positive=[addr])[int(embeded_bin, 2)][0]
                print(addr)
            except:
                water_bin = embeded_bin + water_bin

            # formatting
            # addr

            # dataset[i][addr_first:addr_last+1] = addr

    return

def detector(origin_set, modified_set, group_by, attr_list, water_len, embedding_vec):
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
