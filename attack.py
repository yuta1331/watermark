#!/usr/bin/env python
# coding: utf-8

import api
import consts
from watermark import detector

import pickle
import random
from copy import deepcopy
from collections import OrderedDict


def shuffle_attack(datalist):
    attacked_list = deepcopy(datalist)
    random.shuffle(attacked_list)
    return attacked_list


def add_attack(datalist, attack_num):
    index_added = [random.choice(range(len(datalist)))
                   for _ in range(attack_num)]
    attacked_list = deepcopy(datalist)
    for i in index_added:
        attacked_list.append(datalist[i])
    return index_added, attacked_list


def delete_attack(datalist, attack_num):
    index_deleted = random.sample(range(len(datalist)), attack_num)
    attacked_list = deepcopy(datalist)
    index_deleted.sort(reverse=True)
    for i in index_deleted:
        del attacked_list[i]
    return index_deleted, attacked_list


def collusion_attack(datalists):
    return


if __name__ == '__main__':
    # watermark config
    ORIGINAL_FILE = consts.ORIGIN_FILE
    MODIFIED_FILE = consts.MODIFIED_FILE
    WATERMARK_PICKLE = consts.WATERMARK_PICKLE
    META_DICT_PICKLE = consts.META_DICT_PICKLE
    METHOD = consts.METHOD
    ATTR_LIST = consts.ATTR_LIST
    SENSITIVE = consts.SENSITIVE
    GROUP_BY_ATTR = consts.GROUP_BY_ATTR
    WATER_LEN = consts.WATER_LEN
    MAX_BIN = consts.MAX_BIN

    # test config
    ATTACK_LIST = ['shuffle', 'add', 'del', 'collusion']
    TRIAL_NUM = 10
    MAX_ATTACK_RATE = 250  # permille
    STEP_ATTACK_RATE = 5  # permille
    RESULT_PICKLE = 'result/attack_result.pkl'

    # preparing data
    csv_header, orglist = api.parsed_list(ORIGINAL_FILE, header=True)
    _, modlist = api.parsed_list(MODIFIED_FILE, header=True)

    with open(META_DICT_PICKLE, 'rb') as f:
        meta_dict = pickle.load(f)

    with open(WATERMARK_PICKLE, 'rb') as f:
        watermarked_bin = pickle.load(f)

    group_by = [ATTR_LIST.index(attr) for attr in GROUP_BY_ATTR]

    result_dict = OrderedDict()  # {attack: }

    attack_num_list = list()
    for i in range(0, MAX_ATTACK_RATE + STEP_ATTACK_RATE, STEP_ATTACK_RATE):
        attack_num_list.append((len(orglist) * i) // 1000)
    attack_rate_list = list(
            range(0, MAX_ATTACK_RATE + STEP_ATTACK_RATE, STEP_ATTACK_RATE))

    # attack and try to detect
    for attack in ATTACK_LIST:
        if attack == 'shuffle':
            result_shuffle = list()
            for i in range(TRIAL_NUM):
                attacked_list = shuffle_attack(modlist)
                detected_bin = detector(orglist, attacked_list,
                                        MAX_BIN, meta_dict,
                                        ATTR_LIST, group_by,
                                        WATER_LEN, METHOD)
                bin_similarity = (sum([w == d for w, d
                                      in zip(watermarked_bin,
                                             detected_bin)])
                                  / WATER_LEN)
                result_shuffle.append(bin_similarity)
            result_dict[attack] = result_shuffle

        elif attack == 'add':
            result_add_dict = OrderedDict()
            for attack_rate, attack_num in zip(attack_rate_list,
                                               attack_num_list):
                result_add_list = list()
                for i in range(TRIAL_NUM):
                    index_added, attacked_list =\
                            add_attack(modlist, attack_num)
                    detected_bin = detector(orglist, attacked_list,
                                            MAX_BIN, meta_dict,
                                            ATTR_LIST, group_by,
                                            WATER_LEN, METHOD)
                    bin_similarity = (sum([w == d for w, d
                                          in zip(watermarked_bin,
                                                 detected_bin)])
                                      / WATER_LEN)
                    result_add_list.append(bin_similarity)
                result_add_dict[attack_rate] = result_add_list
            api.csv_composer(csv_header, attacked_list, 'fuga.csv')
            result_dict[attack] = result_add_dict

        elif attack == 'del':
            result_del_dict = OrderedDict()
            for attack_rate, attack_num in zip(attack_rate_list,
                                               attack_num_list):
                result_del_list = list()
                for i in range(TRIAL_NUM):
                    index_deleted, attacked_list =\
                            delete_attack(modlist, attack_num)
                    detected_bin = detector(orglist, attacked_list,
                                            MAX_BIN, meta_dict,
                                            ATTR_LIST, group_by,
                                            WATER_LEN, METHOD)
                    bin_similarity = (sum([w == d for w, d
                                          in zip(watermarked_bin,
                                                 detected_bin)])
                                      / WATER_LEN)
                    result_del_list.append(bin_similarity)
                result_del_dict[attack_rate] = result_del_list
            result_dict[attack] = result_del_dict

        elif attack == 'collusion':
            for i in range(len(modlist)):
                continue

    with open(RESULT_PICKLE, 'wb') as f:
        pickle.dump(result_dict, f)
