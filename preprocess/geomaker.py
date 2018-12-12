# usr/bin/ python
# coding: utf-8
# 住所は国交省の公開データ
# http://nlftp.mlit.go.jp/cgi-bin/isj/dls/_choose_method.cgi

# 目標
# ['茨城県', '～郡～', '～町～一丁目']
# -> ['茨城県', ['～郡', '～'], ['～町', '～'], '1']
# addrgeo_listで管理

# 現状、addr2format_dictとaddr2geo_dictをpickleにて保存

import csv
import pickle
import re
import copy
import os

# in-out file parameter
addr_file = 'addr.csv'
addr2format_pkl = '../pickles/addr2format.pkl'
addr2geo_pkl = '../pickles/addr2geo.pkl'

# regular expression parameter
re_gunshi = re.compile(r'.+[郡市]')
re_cho = re.compile(r'.+町')
re_chome = re.compile(r'[一壱二弐三参四五六七八九十]+丁目')

# substitution parameter
TRANSUNIT = {'一丁目': '1',
             '壱丁目': '1',
             '二丁目': '2',
             '弐丁目': '2',
             '三丁目': '3',
             '参丁目': '3',
             '四丁目': '4',
             '五丁目': '5',
             '六丁目': '6',
             '七丁目': '7',
             '八丁目': '8',
             '九丁目': '9',
             '十丁目': '10',
             '十一丁目': '11',
             '十二丁目': '12',
             '十三丁目': '13',
             '十四丁目': '14',
             '十五丁目': '15',
             '十六丁目': '16',
             '十七丁目': '17',
             '十八丁目': '18',
             '十九丁目': '19',
             }

# tottekuru
addrgeo_list = list()

with open(addr_file, 'r', newline='', encoding='Shift_JISx0213') as f:
    dataReader = csv.reader(f, delimiter=',')
    for row in dataReader:
        addrgeo_list.append([row[1], row[3], row[5], row[6], row[7]])

def splitedAddr(chunk_addr, regex):
    _splitjudge = regex.search(chunk_addr)
    if _splitjudge:
        _split_p = _splitjudge.span()[-1]
        if _split_p < len(chunk_addr):
            return [chunk_addr[:_split_p], chunk_addr[_split_p:]]
    return [chunk_addr]

def chomeTransAddr(chunk_addr, regex, trans):
    # chunk_addrは今リストという仮定
    # ['～町', '～一丁目']とか['～二丁目']
    # -> [['～町', '～'], '1']と[['～'], '2']
    # ['～町', '三丁目']もある

    # 丁目は後ろにあるので[-1]
    _chomejudge = regex.search(chunk_addr[-1])

    if _chomejudge:
        _split_p = _chomejudge.span()[0]
        _chome = chunk_addr.pop(-1)

        if _split_p > 0:
            chunk_addr.append(_chome[:_split_p])

        # 最初からchunk_addrが～丁目のみの場合
        # アラビア数字変換なしで突っ込む。
        elif chunk_addr == []:
            return _chome, '*'

        _chome = trans[_chomejudge.group()]
    else:
        _chome = '*'
    return chunk_addr, _chome


# split&sustitute
for i, addrgeo in enumerate(addrgeo_list):
    # 郡と市のところで分割するよ
    addrgeo_list[i][1] = splitedAddr(addrgeo[1], re_gunshi)

    # 町のところで分割するよ
    addrgeo[2] = splitedAddr(addrgeo[2], re_cho)

    # 丁目を分割してかつアラビア数字に変換するよ
    chunk_addr, chome = chomeTransAddr(addrgeo[2], re_chome, TRANSUNIT)
    addrgeo_list[i][2] = chunk_addr
    addrgeo_list[i].insert(3, chome)

######## addr2format_dictでaddrに対するフォーマットの辞書を管理 #########
# '茨城県水戸市赤塚1' to ['茨城県', '水戸市', '赤塚', '1']
def mask_n_dict(_chunki,\
                sub_list_addr,\
                addr2format_dict):

    _tmp_sub_list_addr = copy.deepcopy(sub_list_addr)
    for i in range(3 - _chunki):
        _tmp_sub_list_addr.append('*')
    addr2format_dict[''.join(sub_list_addr).strip('*')] = _tmp_sub_list_addr
    return

addr_list = list()
for i in range(len(addrgeo_list)):
    addr_list.append(addrgeo_list[i][:4])

# subwordを追加していく
# ['茨城県', ['～郡', '～'], ['～町', '～'], '1']
addr2format_dict = dict()

for _addr in addr_list:
    sub_list_addr = list()

    for _chunki, _chunk in enumerate(_addr):
        if type(_chunk) is list:
            sub_list_addr.append(_chunk[0])
            mask_n_dict(_chunki, sub_list_addr, addr2format_dict)

            for _atom in _chunk[1:]:
                sub_list_addr[_chunki] += _atom
                mask_n_dict(_chunki, sub_list_addr, addr2format_dict)
        else:
            sub_list_addr.append(_chunk)
            mask_n_dict(_chunki, sub_list_addr, addr2format_dict)

from collections import OrderedDict
addr2format_dict = OrderedDict(sorted(addr2format_dict.items()))

########## addr2geo_dictでaddrに対する緯度経度を管理 ###########
# '茨城県水戸市赤塚1' to [30.312, 145.334]
# まず分かっている奴から攻める。
addr2geo_dict = dict()

for _addrgeo in addrgeo_list:
    for i in [1, 2]:
        _addrgeo[i] = ''.join(_addrgeo[i])
    a = ''.join(_addrgeo[:4]).strip('*')
    addr2geo_dict[''.join(_addrgeo[:4])\
                    .strip('*')] = list(map(float, _addrgeo[4:]))



# addr2format_dictのkeyから正規表現しつつ平均を取っていく。
additional_dict = dict()
for _addr in addr2format_dict.keys():
    if _addr not in addr2geo_dict.keys():
        _regex = re.compile(_addr)
        _n = 0
        _lat_sum = 0
        _lng_sum = 0

        for _addr2geo in addr2geo_dict.keys():
            if _regex.match(_addr2geo):
                _n += 1
                _lat_sum += addr2geo_dict[_addr2geo][0]
                _lng_sum += addr2geo_dict[_addr2geo][1]

        additional_dict[_addr] = [_lat_sum / _n,\
                                  _lng_sum / _n]

addr2geo_dict.update(additional_dict)
addr2geo_dict = OrderedDict(sorted(addr2geo_dict.items()))


############### pickle output ##################

if os.path.isdir('../pickles') is False:
    os.mkdir('../pickles')

with open(addr2format_pkl, 'wb') as f:
    pickle.dump(addr2format_dict, f)

with open(addr2geo_pkl, 'wb') as f:
    pickle.dump(addr2geo_dict, f)
