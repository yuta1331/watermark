#!/usr/bin/env/ python
# -*- coding: utf-8 -*-

def quasi_row(row, sensitive):
    if sensitive + 1 < len(row):
        return row[:sensitive] + row[sensitive + 1:]
    return row[:sensitive]

def quasi_list(datalist, sensitive):
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

def calc_k(freqlist):
    min_k = freqlist[0][-1]
    for li in freqlist[1:]: min_k = min(min_k, li[-1])
    return min_k

def k_judge(min_k, k): return min_k >= k

def masking(attr, value): # これ以上一般化できない場合はそのままvalueを返す．
    if attr == 'sex': return value
    if attr == 'time': return value # 今回は'time'がsensitiveなので付け焼刃コーディング

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
        return u'関東'

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

#def datafly(datalist, sensitive, k):


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

    ##### modifying #####
    n = len(datalist)
    m = len(datalist[0])
    for i in range(n):
        for j in range(m):
            datalist[i][j] = masking(attr_list[j], datalist[i][j])
        print(datalist[i])
