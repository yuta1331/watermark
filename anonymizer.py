#!/usr/bin/env/ python

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

def masking(attr, value):
    return '*'

if __name__ == '__main__':
    import subset
    infile = 'hoge.csv'
    sensitive = 9
    k = 3
    init_row, datalist = subset.parsed_list(infile, sensitive)

    ###### frequency ######
    freq = freq_list(datalist, sensitive)

    ##### calc_k #####
    calc_k = calc_k(freq)
    print('k-anonymity: ', calc_k)

    ##### k-judge #####
    kjudge = k_judge(calc_k, k)
    print('k-satisfied: ', kjudge)
    ##### #####
