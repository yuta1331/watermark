#!/usr/bin/env python
# coding: utf-8


import sys
sys.path.append("../")

import consts
import api
from subset.addr_operation import addr_range_catcher
from subset.addr_operation import candidate_addr2geos
from Anonymizer import anonymizer
from subset.addr_operation import local_addr2formatsgeos as la2fg

import pickle
from copy import deepcopy
import unicodedata
import numpy as np

addr_attr = ['addr0', 'addr1', 'addr2', 'addr3', 'addr4']


# categorical tree
def loss(org_value, mod_value, attr, addr2formats, addr2geos, model):
    if org_value == mod_value:
        return 0
    if attr == 'addr':
        cand_addr2geos = candidate_addr2geos(org_value, addr2formats,
                                             addr2geos, model, distance=True)
        if cand_addr2geos == None:
            print('Error: cand_addr2geos')
            print(''.join(org_value).strip('*'))
            print(''.join(mod_value).strip('*'))
        mod_addr = ''.join(mod_value).strip('*')
        if model:
            d = 1 - cand_addr2geos[mod_addr]
            if d < 0:
                d = 0
            max_d = 1 - min(cand_addr2geos.values())
        else:
            d = cand_addr2geos[mod_addr]
            max_d = max(cand_addr2geos.values())
        if max_d > 0:
            return d / max_d
        if d != 0:
            print('d is not 0: d / max_d in loss()')
            print('org_addr: ', org_value)
            print('mod_addr: ', mod_value)
        return d


def left(digit, msg):
    for c in msg:
        if unicodedata.east_asian_width(c) in ('F', 'W', 'A'):
            digit -= 2
        else:
            digit -= 1
    return msg + ' '*digit


class Node:
    def __init__(self):
        self.value = None
        self.leaf_num = 0
        self.children = []
        self.is_leaf = False

    def insert(self, v):
        s = Node()
        s.value = v
        self.children.append(s)

    def show(self, pad):
        print(
            "%s, %s, %d" %
            (left(35, '='*pad + self.value),
             left(5, str(self.is_leaf)),
             self.leaf_num)
             )

    def show_all(self, pad):
        self.show(pad)
        if self.is_leaf:
            return
        else:
            for c in self.children:
                c.show_all(pad + 1)

    def show_children(self, pad):
        self.show(pad)
        if self.is_leaf:
            return
        else:
            for c in self.children:
                c.show(pad + 1)

    def ratio_inverse(self, child_v, child_index=False):
        inverse_sum = 0
        for i, c in enumerate(self.children):
            inverse_sum += 1 / c.leaf_num
            if c.value == child_v:
                child_inverse = 1 / c.leaf_num
                if child_index is True:
                    child_i = i
        try:
            result = child_inverse / inverse_sum * len(self.children)
            if child_index is True:
                return result, child_i
            else:
                return result
        except Exception as e:
            print(':::Error:::')
            print(e.args)
            c.show(1)
            print(child_v)


class GeneralTree:
    def __init__(self):
        self.root = Node()
        self.root.value = None
        self.root.is_leaf = False

    def insert(self, value_l):
        r = self.root

        if r.value is None:
            r.value = value_l[0]
        if r.value != value_l[0]:
            print('Error: top value is not root value')
            print('Error value: ', value_l)

        r.leaf_num += 1

        for value in value_l[1:]:
            for child in r.children:
                if value == child.value:
                    r = child
                    r.leaf_num += 1
                    break
            else:
                r.insert(value)
                r = r.children[-1]
                r.leaf_num += 1
        r.is_leaf = True

    def show(self):
        self.root.show_all(1)

    def search(self, value_l):
        r = self.root
        for value in value_l[1:]:
            for child in r.children:
                if value == child.value:
                    r = child
                    break
        return r

    def hierarchy_num(self, value_l):
        r = self.root
        num = 0
        for value in value_l[1:]:
            for child in r.children:
                if value == child.value:
                    r = child
                    num += 1
                    break
        return num

    def ncp(self, value_l):
        numerator = self.search(value_l).leaf_num
        # print('value: ', value_l)
        # print('numer: ', numerator)
        denominator = self.root.leaf_num
        # print('denom: ', denominator)
        return numerator / denominator

    def ratio_inverse(self, value_l):
        r = self.root
        ratio_sum = 0
        for child_v in value_l[1:]:
            ratio, ci = r.ratio_inverse(child_v, child_index=True)
            ratio_sum += ratio
            r = r.children[ci]
        return ratio_sum

    def general_IL(self, org_value_l, mod_value_l):
        denominator = self.hierarchy_num(org_value_l)
        numerator = denominator - self.hierarchy_num(mod_value_l)
        return numerator / denominator

    def IL_inverse(self, org_value_l, mod_value_l):
        denominator = self.ratio_inverse(org_value_l)
        numerator = denominator - self.ratio_inverse(mod_value_l)
        return numerator / denominator

    def IL_new(self, mod_value_l):
        r = self.root
        result = 1
        for value in mod_value_l[1:]:
            result /= len(r.children)
            for child in r.children:
                if value == child.value:
                    r = child
                    break
        return result

    def IL_tree(self, org_value_l, mod_value_l):
        size_org_v = self.search(org_value_l).leaf_num
        size_mod_v = self.search(mod_value_l).leaf_num
        return (size_mod_v - size_org_v) / (self.root.leaf_num - size_org_v)


    '''
    def extended_IL_inverse(self, 
                            org_value_l,
                            ano_value_l,
                            wat_value_l,
                            addr2formats,
                            addr2geos):
        denominator = self.ratio_inverse(org_value_l)
        numerator = denominator - self.ratio_inverse(mod_value_l)
        parent_IL = self.search(ano_value_l[:-1])\
                        .ratio_inverse(ano_value_l[-1])
        parent_loss = loss(ano_value_l, wat_value_l,
                           attr, addr2formats, addr2geos)
        numerator += parent_IL * parent_loss
        return numerator / denominator
    '''


# address calculator
def general_addr(addr_attr, addr):
    general = list()
    prev = addr
    if prev[0] == '関東':
        general.append(addr[0])
        return general
    while(True):
        if ('*' in prev) and (prev.index('*') == 1):
            general.append(prev[0])
            now = anonymizer.address_masking(addr_attr, deepcopy(prev))
            general.append(now[0])
            break

        now = anonymizer.address_masking(addr_attr, deepcopy(prev))

        str_prev = ''.join(prev).strip('*')
        str_now = ''.join(now).strip('*')

        for chunk in str_now:
            str_prev = str_prev[1:]
        general.append(str_prev)

        prev = now

    return general[::-1]


def general_addrs(addr_attr, addr_l):
    general_l = list()
    for addr in addr_l:
        general_l.append(general_addr(addr_attr, deepcopy(addr)))
    return general_l


class AddrTree(GeneralTree):
    def extended_general_IL(self,
                            org_addr,
                            ano_addr,
                            wat_addr,
                            addr2formats,
                            addr2geos,
                            model):
        general_org_addr = general_addr(addr_attr, org_addr)
        general_ano_addr = general_addr(addr_attr, ano_addr)
        general_wat_addr = general_addr(addr_attr, wat_addr)

        if general_ano_addr == general_wat_addr:
            return self.general_IL(general_org_addr, general_ano_addr)

        denominator = self.hierarchy_num(general_org_addr)
        numerator = (denominator
                    - self.hierarchy_num(general_ano_addr)
                    + loss(ano_addr, wat_addr, 'addr',
                           addr2formats, addr2geos, model))
        return numerator / denominator

    def extended_IL_inverse(self,
                            org_addr,
                            ano_addr,
                            wat_addr,
                            addr2formats,
                            addr2geos,
                            model):
        general_org_addr = general_addr(addr_attr, org_addr)
        general_ano_addr = general_addr(addr_attr, ano_addr)
        general_wat_addr = general_addr(addr_attr, wat_addr)

        if general_ano_addr == general_wat_addr:
            return self.IL_inverse(general_org_addr, general_ano_addr)

        denominator = self.ratio_inverse(general_org_addr)

        numerator = denominator - self.ratio_inverse(general_ano_addr)
        parent_IL = self.search(general_ano_addr[:-1])\
                        .ratio_inverse(general_ano_addr[-1])
        parent_loss = loss(ano_addr, wat_addr, 'addr',
                           addr2formats, addr2geos, model)
        numerator += parent_IL * parent_loss

        return numerator / denominator

    def extended_IL_new(self, ano_addr, wat_addr):
        general_ano_addr = general_addr(addr_attr, ano_addr)
        general_wat_addr = general_addr(addr_attr, wat_addr)

        r = self.root
        result = 1
        for i, value in enumerate(general_wat_addr[1:]):
            for child in r.children:
                if value == child.value:
                    result /= len(r.children)

                    # modified by watermarking
                    if value != general_ano_addr[i+1]:
                        result *= 2

                    r = child
                    break
        return result

    def extended_IL_tree(self, org_addr, ano_addr, wat_addr):
        general_org_addr = general_addr(addr_attr, org_addr)
        general_ano_addr = general_addr(addr_attr, ano_addr)
        general_wat_addr = general_addr(addr_attr, wat_addr)
        size_org_v = self.search(general_org_addr).leaf_num
        size_ano_v = self.search(general_ano_addr).leaf_num

        if ano_addr == wat_addr:
            size_wat_v = 0
        else:
            size_wat_v = self.search(general_wat_addr).leaf_num

        return ((size_ano_v + size_wat_v - size_org_v)
                / (self.root.leaf_num - size_org_v))


def cast_sequential_num2int(dataset):
    for record in dataset:
        record.append(int(record.pop()))


def insert_empty(dataset):
    for i, record in enumerate(dataset):
        if i != record[-1]:
            dataset.insert(i, ['empty', i])


def fix_addr(dataset, addr_first, addr_last):
    # dataset has been inserted 'empty'
    addr_l = list()
    for record in dataset:
        if record[0] == 'empty':
            addr_l.append(['関東', '*', '*', '*', '*'])
        else:
            addr_l.append(record[addr_first:addr_last+1])
    return addr_l


def IL_calc(org_l, mod_l, wat_l, attr_list,
            addr2formats, addr2geos, IL_mode, model):
    # sequential numberをintに
    cast_sequential_num2int(org_l)
    cast_sequential_num2int(mod_l)
    cast_sequential_num2int(wat_l)

    # sort by sequential number
    org_l.sort(key=lambda x: x[-1])
    mod_l.sort(key=lambda x: x[-1])
    wat_l.sort(key=lambda x: x[-1])

    # insert empty record to mod_l and wat_l
    insert_empty(mod_l)
    insert_empty(wat_l)

    # IL of addr
    addr_first, addr_last = addr_range_catcher(attr_list)

    ## get original addr list
    org_addr_l = [x[addr_first:addr_last+1] for x in org_l]

    ## get modified addr list and watermarked addr list
    mod_addr_l = fix_addr(mod_l, addr_first, addr_last)
    wat_addr_l = fix_addr(wat_l, addr_first, addr_last)

    ## address tree from original addr list
    addr_tree = AddrTree()

    org_general_addr_l = general_addrs(addr_attr, org_addr_l)
    for addr in org_general_addr_l:
        addr_tree.insert(addr)

    # addr_tree.show()
    # addr_tree.root.show_children(1)

    ## IL calculation
    mod_general_addr_l = general_addrs(addr_attr, mod_addr_l)

    IL_list = list()


    if IL_mode == 'NCP':
        # NCP
        for mod_addr in mod_general_addr_l:
            IL_list.append(addr_tree.ncp(mod_addr))
    elif IL_mode == 'general':
        if consts.MODE == 'proposal':
            for org_addr, mod_addr, wat_addr in zip(org_addr_l,
                                                    mod_addr_l,
                                                    wat_addr_l):
                IL_list.append(addr_tree\
                               .extended_general_IL(org_addr,
                                                    mod_addr,
                                                    wat_addr,
                                                    addr2formats,
                                                    addr2geos,
                                                    model))
        elif consts.MODE == 'existing':
            for org_addr, wat_addr in zip(org_addr_l, wat_addr_l):
                general_org_addr = general_addr(addr_attr, org_addr)
                general_wat_addr = general_addr(addr_attr, wat_addr)
                IL_list.append(addr_tree.general_IL(general_org_addr,
                                                    general_wat_addr))

    elif IL_mode == 'inverse':
        # IL_inverse: extended
        if consts.MODE == 'proposal':
            for org_addr, mod_addr, wat_addr in zip(org_addr_l,
                                                    mod_addr_l,
                                                    wat_addr_l):
                IL_list.append(addr_tree\
                               .extended_IL_inverse(org_addr,
                                                    mod_addr,
                                                    wat_addr,
                                                    addr2formats,
                                                    addr2geos,
                                                    model))

        # IL_inverse: not extended for existing method
        elif consts.MODE == 'existing':
            for org_addr, wat_addr in zip(org_addr_l, wat_addr_l):
                general_org_addr = general_addr(addr_attr, org_addr)
                general_wat_addr = general_addr(addr_attr, wat_addr)
                IL_list.append(addr_tree.IL_inverse(general_org_addr,
                                                    general_wat_addr))
    elif IL_mode == 'new':
        # extended
        if consts.MODE == 'proposal':
            for org_addr, mod_addr, wat_addr in zip(org_addr_l,
                                                    mod_addr_l,
                                                    wat_addr_l):
                IL_list.append(addr_tree.extended_IL_new(mod_addr,
                                                         wat_addr))

        # not extended for existing method
        elif consts.MODE == 'existing':
            for wat_addr in wat_addr_l:
                general_wat_addr = general_addr(addr_attr, wat_addr)
                IL_list.append(addr_tree.IL_new(general_wat_addr))

    elif IL_mode == 'tree':
        # extended
        if consts.MODE == 'proposal':
            for org_addr, mod_addr, wat_addr in zip(org_addr_l,
                                                    mod_addr_l,
                                                    wat_addr_l):
                IL_list.append(addr_tree.extended_IL_tree(org_addr,
                                                          mod_addr,
                                                          wat_addr))

        # not extended for existing method
        elif consts.MODE == 'existing':
            for org_addr, wat_addr in zip(org_addr_l, wat_addr_l):
                general_org_addr = general_addr(addr_attr, org_addr)
                general_wat_addr = general_addr(addr_attr, wat_addr)
                IL_list.append(addr_tree.IL_tree(general_org_addr,
                                                 general_wat_addr))

    return IL_list, mod_addr_l


if __name__ == '__main__':
    from subset import embedding_operation

    attr_list = consts.ATTR_LIST
    attr_list.append('seq')

    original_file = 'original_data.csv'
    anonymized_file = '../' + consts.ORIGIN_FILE
    watermarked_file = '../' + consts.MODIFIED_FILE

    csv_header, org_list = api.parsed_list(original_file, True)
    _, anonymized_list = api.parsed_list(anonymized_file, True)
    _, watermarked_list = api.parsed_list(watermarked_file, True)

    with open('../pickles/addr2format.pkl', 'rb') as f:
        addr2formats = pickle.load(f)
    with open('../pickles/addr2geo.pkl', 'rb') as f:
        addr2geos = pickle.load(f)

    # for embedding
    IS_EMBEDDING = True
    MODEL = '../../models/model1/model_50.bin'

    # embedding mode
    # watermarkで使わないとしても，ILの計算で使う
    model = embedding_operation.load_model(MODEL)
    if IS_EMBEDDING:
        model_for_watermark = model
    else:
        model_for_watermark = None

    # localized dictionaries
    local_addr2formats, local_addr2geos =\
        la2fg(attr_list, anonymized_list, addr2formats, addr2geos)

    # IL_mode = 'NCP'
    IL_mode = 'general'
    # IL_mode = 'inverse'
    # IL_mode = 'new'
    # IL_mode = 'tree'
    IL_list, anonym_addr_l = IL_calc(org_list,
                                     anonymized_list,
                                     anonymized_list,
                                     attr_list,
                                     local_addr2formats,
                                     local_addr2geos,
                                     IL_mode,
                                     model)
    print('max: ', max(IL_list))
    print('min: ', min(IL_list))
    print('IL: ', np.mean(IL_list))

    IL_list, anonym_addr_l = IL_calc(org_list,
                                     anonymized_list,
                                     watermarked_list,
                                     attr_list,
                                     local_addr2formats,
                                     local_addr2geos,
                                     IL_mode,
                                     model)
    print('max: ', max(IL_list))
    print('min: ', min(IL_list))
    print('IL: ', np.mean(IL_list))

    '''
    for mod_addr, IL in zip(anonym_addr_l, IL_list):
        print('mod: ', mod_addr)
        print('IL : ', IL)
    '''
