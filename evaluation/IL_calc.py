#!/usr/bin/env python
# coding: utf-8


import sys
sys.path.append("../")

import consts
import api
from subset.addr_operation import addr_range_catcher
from subset.addr_operation import candidate_addr2geos
from Anonymizer import anonymizer

import pickle
from copy import deepcopy
import unicodedata
import numpy as np

addr_attr = ['addr0', 'addr1', 'addr2', 'addr3', 'addr4']

# categorical tree
def loss(org_value, mod_value, attr, addr2formats, addr2geos):
    if org_value == mod_value:
        return 0
    if attr == 'addr':
        cand_addr2geos = candidate_addr2geos(org_value, addr2formats,
                                             addr2geos, distance=True)
        mod_addr = ''.join(mod_value).strip('*')
        d = cand_addr2geos[mod_addr]
        max_d = max(cand_addr2geos.values())
        return d / max_d


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

    def IL_inverse(self, org_value_l, mod_value_l):
        denominator = self.ratio_inverse(org_value_l)
        numerator = denominator - self.ratio_inverse(mod_value_l)
        return numerator / denominator

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
    def extended_IL_inverse(self, 
                            org_addr,
                            ano_addr,
                            wat_addr,
                            addr2formats,
                            addr2geos):
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
                           addr2formats, addr2geos)
        numerator += parent_IL * parent_loss

        return numerator / denominator


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


def IL_calc(org_l, mod_l, wat_l, attr_list, addr2formats, addr2geos):
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

    IL_method = 'inverse'

    if IL_method == 'NCP':
        # NCP
        for mod_addr in mod_general_addr_l:
            IL_list.append(addr_tree.ncp(mod_addr))
    elif IL_method == 'inverse':
        # IL_inverse: extended
        for org_addr, mod_addr, wat_addr in zip(org_addr_l,
                                                mod_addr_l,
                                                wat_addr_l):
            IL_list.append(addr_tree\
                           .extended_IL_inverse(org_addr,
                                                mod_addr,
                                                wat_addr,
                                                addr2formats,
                                                addr2geos))

    return IL_list, mod_addr_l


if __name__ == '__main__':
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

    IL_list, anonym_addr_l = IL_calc(org_list,
                                     anonymized_list,
                                     anonymized_list,
                                     attr_list,
                                     addr2formats,
                                     addr2geos)
    print('max: ', max(IL_list))
    print('min: ', min(IL_list))
    print('IL: ', np.mean(IL_list))

    IL_list, anonym_addr_l = IL_calc(org_list,
                                     anonymized_list,
                                     watermarked_list,
                                     attr_list,
                                     addr2formats,
                                     addr2geos)
    print('max: ', max(IL_list))
    print('min: ', min(IL_list))
    print('IL: ', np.mean(IL_list))

    '''
    for mod_addr, IL in zip(anonym_addr_l, IL_list):
        print('mod: ', mod_addr)
        print('IL : ', IL)
    '''
