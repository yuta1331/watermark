#!/usr/bin/env/ python
# -*- coding: utf-8 -*-

from copy import deepcopy

def quasi_row(row, sensitive):
    if sensitive + 1 < len(row):
        return row[:sensitive] + row[sensitive + 1:]
    return row[:sensitive]

def quasi_list(datalist, sensitive):
    if sensitive == None: return deepcopy(datalist)
    quasilist = list()
    for i in range(len(datalist)):
        quasilist.append(quasi_row(datalist[i], sensitive))
    return quasilist

def freq_list(datalist, sensitive): # calculate the frequency of each q*-block
                                    # 最後尾要素にfrequency
    quasilist = quasi_list(datalist, sensitive)
    i = 0
    while i < len(quasilist):
        quasilist[i].append(1)
        j = i + 1
        while j < len(quasilist):
            if quasilist[i][:-1] == quasilist[j]:
                quasilist[i][-1] += 1 # frequency increment
                del quasilist[j]
            else:
                j += 1
        i += 1
    return quasilist

def attr_search(freqlist, data, attr_i):
    for i, attr in enumerate(freqlist):
        if data[attr_i] == attr[0]:
            freqlist[i][1] += 1
            return
    freqlist.append([data[attr_i], 1]) # Unless objective attr is found
    return

def freq_attr_list(datalist, attr_i): # [value, freq]
    freq_attrlist = list()
    for data in datalist: # datalistを行ごとに読み込む
        attr_search(freq_attrlist, data, attr_i)
    return freq_attrlist

def calc_k(freqlist):
    min_k = freqlist[0][-1]
    for li in freqlist[1:]: min_k = min(min_k, li[-1])
    return min_k

def k_judge(min_k, k): return min_k >= k

def masking(attr, value): # これ以上一般化できない場合はそのままvalueを返す．
    if attr == 'sex': return value

    # 今回は'time'がsensitiveなので付け焼刃コーディング
    if attr == 'time': return value

    mask = value.find('*')
    if mask == 0: return value # 先頭が既に'*'ならそのまま返す．

    #### 以下属性ごとのマスキング処理 ####
    if attr == 'tel':
        if mask == -1: return value[:mask] + '*'
        else: return value[:mask-1] + '*' + value[mask:]

    elif attr == 'poscode':
        dash = value.find('-')
        if mask == -1: return value[:mask] + '*'
        elif mask == dash + 1: return value[:dash-1] + value[dash:]
        else: return value[:mask-1] + value[mask:]

    elif attr == 'add0':
        return '関東' # 今は関東のみなのでこれで

    elif attr in ['add1', 'add2']:
        return '*'

    elif attr == 'add3':
        rdash = value.rfind('-')
        if rdash == -1:
            return '*'
        else:
            return value[:rdash]

    elif attr == 'add4':
        return '*'

    elif attr == 'birth':
        slash = value.rfind('/')
        if slash == -1:
            if mask == -1: return value[:mask] + '*'
            else: return value[:mask-1] + '*' + value[mask:]
        else: return value[:slash]

def address_masking(add_attr, address):
# address = ['群馬県', '安中市', '岩井', '1-17-1', 'タワー岩井31']
    try:
        i = address.index('*') - 1
    except:
        i = -1
    address[i] = masking(add_attr[i], address[i])
    return address

# kを満たしていないq*-blockを取り出す
def no_secure_blocks(freq_list, k):
    return [x[:-1] for x in freq_list if x[-1] < k]

# 住所はひとかたまりで一般化すべきなのでここでindexを得る
def address_grouper(attr_list):
    try:
        first = attr_list.index('poscode')
    except:
        for i in range(len(attr_list)):
            if 'add' in attr_list[i]:
                first = i
                break
    for i in range(len(attr_list))[::-1]:
        if 'add' in attr_list[i]:
            last = i
            return first, last

def no_secure_add_blocks(add_first, add_last, datalist, k):
    addlist_in_datalist = list()
    for data in datalist:
        addlist_in_datalist.append(data[add_first:add_last+1])
    add_freq_list = freq_list(addlist_in_datalist, None)
    return no_secure_blocks(add_freq_list, k)


def datafly(datalist, attr_list, sensitive, k):

    # まずは住所を一般化する
    add_first, add_last = address_grouper(attr_list)
    pos_frag = 0
    if attr_list[add_first] == 'poscode':
        add_first += 1
        pos_frag = 1

    nosecure_add_blocks = \
        no_secure_add_blocks(add_first, add_last, datalist, k)

    while len(nosecure_add_blocks) > 0:
        for i, data in enumerate(datalist):
            if data[add_first:add_last+1] in nosecure_add_blocks:
                tmp = address_masking(attr_list[add_first:add_last+1], \
                                      data[add_first:add_last+1])
                datalist[i][add_first:add_last+1] = tmp
        nosecure_add_blocks = \
            no_secure_add_blocks(add_first, add_last, datalist, k)

    ''' for debug
    addlist_in_datalist = list()
    for data in datalist:
        addlist_in_datalist.append(data[add_first:add_last+1])
    add_freq_list = freq_list(addlist_in_datalist, None)
    subset.all_sorted_list(add_freq_list, None)
    for x in add_freq_list:
        print(x)
    '''

    '''
    for attr_i in range(len(datalist[0])):
        freq_attrlist = freq_attr_list(datalist, attr_i)
        for value_freq in freq_attrlist:
            if value_freq[1] < k:
                for j, data in enumerate(datalist):
                    if data[attr_i] == value_freq[0]:
                        datalist[j][attr_i] = \
                            masking(attr_list[attr_i], datalist[j][attr_i])
    '''
    return


if __name__ == '__main__':
    import subset
    infile = 'original_data.csv'
    sensitive = 9
    k = 3
    attr_list = ['sex', 'tel',
             'poscode', 'add0', 'add1', 'add2', 'add3', 'add4',
             'birth', 'time'] # attributes of infile
    init_row, datalist = subset.parsed_list(infile, sensitive)

    ###### frequency ######
    freq = freq_list(datalist, sensitive)

    ##### calc_k #####
    calc_k = calc_k(freq)
    print('k-anonymity: ', calc_k)

    ##### k-judge #####
    kjudge = k_judge(calc_k, k)
    print('k-satisfied: ', kjudge)

    ##### freq_attr_list #####
    '''
    a = freq_attr_list(datalist, attr_list.index('add0'))
    print(a)
    '''

    ##### modifying #####
    '''
    n = len(datalist)
    m = len(datalist[0])
    for i in range(n):
        for j in range(m):
            datalist[i][j] = masking(attr_list[j], datalist[i][j])
        #print(datalist[i])
    '''

    ##### datafly #####
    datafly(datalist, attr_list, sensitive, k)
    for data in datalist:
        print(data)
