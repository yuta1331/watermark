#! usr/bin/env python
# -*- coding: utf-8 -*-

import re

import subset

def address_grouper(attr_list):
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

def watermarker(dataset, group_by, water_bin, attr_list):
    dataset = subset.sorted_list(dataset, group_by)

    # グループごとに埋め込み
    tmp_group_key = list()
    for record in dataset:
        if len(water_bin) == 0:
            break

        data_key = [record[i] for i in group_by]

        # 今はグループに1つだけ編集
        # 住所のみ
        if len(tmp_group_key) == 0 or tmp_group_key != data_key:
            tmp_group_key = data_key
            embeded_bin = water_bin[:2]
            water_bin = water_bin[2:]

            # 住所を取り出す
            # 住所はまとめてくっつける
            addr_first, addr_last = address_grouper(attr_list)
            address = ''.join(record[addr_first:addr_last+1])
            address = re.sub(r'\*+', '', address)

            # modifying

            # formatting
            # address

            # dataset[i][addr_first:addr_last+1] = address

    return
