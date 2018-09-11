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
        if len(value) != 10: return value + '*'
        elif mask == -1: return value[:mask] + '*'
        elif mask == 1: return '**********'
        else: return value[:mask-1] + '*' + value[mask:]

    elif attr == 'poscode':
        dash = value.find('-')

        # '*'がなければ
        if mask == -1: return value[:mask] + '*'

        # '*'の左が'-'なら
        elif mask == dash + 1: return value[:dash-1] + '*' + value[dash:]

        # 上記以外
        else: return value[:mask-1] + '*' + value[mask:]

    elif attr == 'addr0':
        return '関東' # 今は関東のみなのでこれで

    elif attr in ['addr1', 'addr2']:
        return '*'

    elif attr == 'addr3':
        rdash = value.rfind('-')
        if rdash == -1:
            return '*'
        else:
            return value[:rdash]

    elif attr == 'addr4':
        return '*'

    elif attr == 'birth':
        slash = value.rfind('/')
        if slash == -1:
            if mask == -1:return value[:mask] + '*'
            else: return value[:mask-1] + '*' + value[mask:]
        else: return value[:slash]

def address_masking(addr_attr, address):
# address = ['群馬県', '安中市', '岩井', '1-17-1', 'タワー岩井31']
    try:
        i = address.index('*') - 1
    except:
        i = -1
    address[i] = masking(addr_attr[i], address[i])
    return address

# kを満たしていないq*-blockを取り出す
def no_secure_blocks(freq_list, k):
    return [x[:-1] for x in freq_list if x[-1] < k]

# 属性ごとでkを満たしていないblockを取り出す
def no_secure_attrs(attr_first, attr_last, datalist, k):
    attrlist_in_datalist = list()
    for data in datalist:
        attrlist_in_datalist.append(data[attr_first:attr_last+1])
    attr_freq_list = freq_list(attrlist_in_datalist, None)
    return no_secure_blocks(attr_freq_list, k)

# 住所はひとかたまりで一般化すべきなのでここでindexを得る
def address_grouper(attr_list):
    try:
        first = attr_list.index('poscode')
    except:
        for i in range(len(attr_list)):
            if 'addr' in attr_list[i]:
                first = i
                break
    for i in range(len(attr_list))[::-1]:
        if 'addr' in attr_list[i]:
            last = i
            return first, last

def datafly(datalist, attr_list, sensitive, k):

    # とりあえず各属性でkを満たすようにする

    # まずは住所を一般化する
    addr_first, addr_last = address_grouper(attr_list)
    pos_frag = 0
    if attr_list[addr_first] == 'poscode':
        addr_first += 1
        pos_frag = 1

    nosecure_addrs = \
        no_secure_attrs(addr_first, addr_last, datalist, k)

    # poscodeは除く
    while len(nosecure_addrs) > 0:
        for i, data in enumerate(datalist):
            if data[addr_first:addr_last+1] in nosecure_addrs:
                tmp = address_masking(attr_list[addr_first:addr_last+1], \
                                      data[addr_first:addr_last+1])
                datalist[i][addr_first:addr_last+1] = tmp
        nosecure_addrs = \
            no_secure_attrs(addr_first, addr_last, datalist, k)


    '''# for debug
    addrlist_in_datalist = list()
    for data in datalist:
        addrlist_in_datalist.append(data[addr_first:addr_last+1])
    addr_freq_list = freq_list(addrlist_in_datalist, None)
    subset.all_sorted_list(addr_freq_list, None)
    for x in addr_freq_list:
        print(x)
    '''

    # 住所以外
    range_except_addr = list(range(0, addr_first))
    range_except_addr.extend(list(range(addr_last+1, len(attr_list))))
    range_except_addr.remove(sensitive)
    for attr_i in range_except_addr:
        nosecure_attrs = no_secure_attrs(attr_i, attr_i, datalist, k)
        while len(nosecure_attrs) > 0:
            if len(nosecure_attrs) == 1: break
            for i, data in enumerate(datalist):
                if [data[attr_i]] in nosecure_attrs:
                    datalist[i][attr_i] = masking(attr_list[attr_i], data[attr_i])
            nosecure_attrs = no_secure_attrs(attr_i, attr_i, datalist, k)

        # for debug
        freq_attrlist = freq_attr_list(datalist, attr_i)
        for i in range(2):
            freq_attrlist.sort(key=lambda x:x[i], reverse=True)
        for x in freq_attrlist:
            print(x)


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
             'poscode', 'addr0', 'addr1', 'addr2', 'addr3', 'addr4',
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
    a = freq_attr_list(datalist, attr_list.index('addr0'))
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
    subset.all_sorted_list(datalist, sensitive)
    for data in datalist:
        print(data)
