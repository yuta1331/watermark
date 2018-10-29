# usr/bin/ python
# coding: utf-8

import xmltodict
import requests
from math import radians, sin, cos, sqrt
from statistics import mean

# 住所を入力したら緯度経度が返ってくる関数
def AddrtoLocate(address):
    url = 'http://www.geocoding.jp/api/'
    payload = {'q':address}
    result = requests.get(url, params=payload)
    resultdict = xmltodict.parse(result.text)
    resultlocate = resultdict["result"]["coordinate"]
    return resultlocate["lat"], resultlocate["lng"]


def distance(locate1, locate2):
    # 緯度経度をラジアンに変換
    rlat1 = radians(float(locate1[0]))
    rlng1 = radians(float(locate1[1]))
    rlat2 = radians(float(locate2[0]))
    rlng2 = radians(float(locate2[1]))
    
    # 緯度差と経度差
    rlat_diff = rlat1 - rlat2
    rlng_diff = rlng1 - rlng2
    
    # 平均緯度
    rlat_avg = mean([rlat1, rlat2])
    
    # 測地系による値の違い
    # 赤道半径
#    a = 6378137.0 # world
    a = 6377397.155  # japan
    
    # 極半径
#    b = 6378137.0 # world
    b = 6356078.963  # japan
    
    # 第一離心率^2
    e2 = (pow(a, 2) - pow(b, 2)) / pow(a, 2)
    
    # 赤道上の子午線曲率半径
    a1e2 = a * (1 - e2)
    
    sinLat = sin(rlat_avg)
    w2 = 1.0 - e2 * pow(sinLat, 2)
    
    # 子午線曲率半径m
    m = a1e2 / (sqrt(w2) * w2)
    
    # 卯酉線曲率半径n
    n = a / sqrt(w2)
    
    # 算出
    t1 = m * rlat_diff
    t2 = n * cos(rlat_avg) * rlng_diff
    distance = sqrt(pow(t1, 2) + pow(t2, 2))
    return distance / 1000

if __name__ == '__main__':
    locate1 = AddrtoLocate("東京都")
    print(locate1)
    locate2 = AddrtoLocate("埼玉県")
    print(locate2)
    print(distance(locate1, locate2))
