#!/usr/bin/env python
# coding: utf-8

import api
import consts
from watermark import detector
from subset import embedding_operation
from subset import turbo
from subset import aes_ECB

import pickle
import random
from copy import deepcopy
from collections import OrderedDict
import math
import gmpy2

import sys


def shuffle_attack(datalist):
    attacked_list = deepcopy(datalist)
    random.shuffle(attacked_list)
    return attacked_list


def add_attack(datalist, index_adds):
    attacked_list = deepcopy(datalist)
    for i in index_adds:
        attacked_list.append(datalist[i])
    return attacked_list


def delete_attack(datalist, index_dels):
    attacked_list = deepcopy(datalist)
    index_dels.sort(reverse=True)
    for i in index_dels:
        del attacked_list[i]
    return attacked_list


def replace_attack(datalist, index_replaces, index_copieds):
    attacked_list = deepcopy(datalist)
    for index_replace, index_copied in zip(index_replaces, index_copieds):
        attacked_list[index_replace] = datalist[index_copied]
    return attacked_list


def collusion_attack(datalists):
    return


if __name__ == '__main__':
    # watermark config
    METHOD = consts.METHOD
    ATTR_LIST = consts.ATTR_LIST
    SENSITIVE = consts.SENSITIVE
    GROUP_BY_ATTR = consts.GROUP_BY_ATTR
    WATER_BYTE = consts.WATER_BYTE
    MAX_BIN = consts.MAX_BIN

    # test config
    MAX_EXTRACTED_LEN = 600
    ATTACK_LIST = ['shuffle', 'add', 'del', 'replace', 'collusion']
    TRIAL_NUM = 20

    PERCENT = 100
    PERMILLE = 1000
    MAX_ATTACK_RATE = PERCENT
    STEP_ATTACK_RATE = 5

    IS_ATTACK_PICKLE = True

    RESULT_PICKLE = 'result/attack_result_existing.pkl'

    # preparing data
    csv_header, orglist = api.parsed_list(consts.ORIGIN_FILE, header=True)
    _, modlist = api.parsed_list(consts.MODIFIED_FILE, header=True)

    with open(consts.META_DICT_PICKLE, 'rb') as f:
        meta_dict = pickle.load(f)

    ## prepare watermark
    with open(consts.WATERMARK_PICKLE, 'rb') as f:
        watermark = pickle.load(f)
    with open(consts.AES_KEY_PICKLE, 'rb') as f:
        aes_key = pickle.load(f)
    cipher = aes_ECB.AESCipher(aes_key)
    watermark_bin = cipher.encrypt(watermark)

    water_len = math.ceil((WATER_BYTE + 1) / 16) * 128

    group_by = [ATTR_LIST.index(attr) for attr in GROUP_BY_ATTR]

    result_dict = OrderedDict()  # {attack: }

    attack_rate_list = list(
            range(0, MAX_ATTACK_RATE + STEP_ATTACK_RATE, STEP_ATTACK_RATE))

    attack_num_list = [(len(orglist) * i) // MAX_ATTACK_RATE
                       for i in attack_rate_list]

    ## prepare attack indexes
    def index_(pickle_file, is_dx):
        if IS_ATTACK_PICKLE:
            with open(pickle_file, 'rb') as f:
                return pickle.load(f)
        index_dict = OrderedDict()
        for attack_num in attack_num_list:
            index_dict[attack_num] = list()
            for i in range(TRIAL_NUM):
                if is_dx:
                    indexes = [random.choice(range(len(modlist)))
                                 for _ in range(attack_num)]
                    index_dict[attack_num].append(indexes)

                else:
                    indexes = random.sample(range(len(modlist)), attack_num)
                    index_dict[attack_num].append(indexes)

        with open(pickle_file, 'wb') as f:
            pickle.dump(index_dict, f)
        return index_dict

    ### addition attack
    index_adds_list_dict = index_('pickles/index_adds.pkl', is_dx=True)

    ### deletion attack
    index_dels_list_dict = index_('pickles/index_dels.pkl', is_dx=False)

    ### replacement attack
    #### 置換先
    index_replaces_list_dict = index_('pickles/index_replaces.pkl', is_dx=False)
    #### 置換元
    index_copieds_list_dict = index_('pickles/index_copieds.pkl', is_dx=True)


    ## embedding mode
    if consts.IS_EMBEDDING:
        model = embedding_operation.load_model(consts.MODEL)
    else:
        model = None


    def detection_precision(attacked_list):
        detected_bin = detector(orglist, attacked_list,
                                MAX_BIN, meta_dict,
                                ATTR_LIST, group_by,
                                water_len*2, METHOD, model)

        # デカくなりすぎるため
        detected_bin = detected_bin[:MAX_EXTRACTED_LEN]

        detected_data = detected_bin[:len(detected_bin)//2]
        detected_parity = detected_bin[len(detected_bin)//2:]

        if consts.IS_USED_AES:
            detected_data += '0'*((128 - (len(detected_bin)//2)%128)%128)

            pad_num = (128 - (len(detected_bin) - len(detected_bin)//2)%128)%128
            detected_parity += '0' *pad_num

        if gmpy2.popcount(int(detected_data, 2)) == 0:
            data = detected_data
        else:
            data, num_of_loop = turbo.decode(detected_data, detected_parity,
                                             400, True)
            if data == '':
                data = detected_data
        bin_similarity = (sum([w == d for w, d in zip(watermark_bin,
                                                      data)])
                          / water_len
                          * 100)

        return bin_similarity


    # attack and try to detect
    print('TRIAL_NUM: ' , TRIAL_NUM)
    for attack in ATTACK_LIST:
        sys.stdout.write('\n')
        print(attack)

        if attack == 'shuffle':
            result_shuffle = list()
            for i in range(TRIAL_NUM):
                attacked_list = shuffle_attack(modlist)
                bin_similarity = detection_precision(attacked_list)
                result_shuffle.append(bin_similarity)

                sys.stdout.write('#')
                sys.stdout.flush()

            result_dict[attack] = result_shuffle

        elif attack == 'add':
            result_add_dict = OrderedDict()
            total_len = OrderedDict()
            for attack_rate, attack_num in zip(attack_rate_list,
                                               attack_num_list):
                sys.stdout.write('\n')
                print(attack)
                print(' attack_rate: ', str(attack_rate))

                result_add_list = list()
                total_len[attack_rate] = list()

                for index_adds in index_adds_list_dict[attack_num]:
                    attacked_list = add_attack(modlist, index_adds)

                    attacked_list = shuffle_attack(attacked_list)
                    total_len[attack_rate].append(len(attacked_list))

                    # detection and calculation of precision
                    bin_similarity = detection_precision(attacked_list)
                    result_add_list.append(bin_similarity)

                    sys.stdout.write('#')
                    sys.stdout.flush()

                result_add_dict[attack_rate] = result_add_list
            result_dict[attack] = result_add_dict

        elif attack == 'del':
            result_del_dict = OrderedDict()
            for attack_rate, attack_num in zip(attack_rate_list,
                                               attack_num_list):
                sys.stdout.write('\n')
                print(attack)
                print(' attack_rate: ', str(attack_rate))

                result_del_list = list()
                for index_dels in index_dels_list_dict[attack_num]:
                    attacked_list = delete_attack(modlist, index_dels)

                    try:
                        # detection and calculation of precision
                        bin_similarity = detection_precision(attacked_list)
                        result_del_list.append(bin_similarity)

                    except IndexError:
                        data = '0' * water_len
                        bin_similarity = (sum([w == d
                                            for w, d in zip(watermark_bin,
                                                            data)])
                                          / water_len
                                          * 100)

                        result_del_list.append(bin_similarity)

                    sys.stdout.write('#')
                    sys.stdout.flush()

                result_del_dict[attack_rate] = result_del_list
            result_dict[attack] = result_del_dict

        elif attack == 'replace':
            result_replace_dict = OrderedDict()
            for attack_rate, attack_num in zip(attack_rate_list,
                                               attack_num_list):
                sys.stdout.write('\n')
                print(attack)
                print(' attack_rate: ', str(attack_rate))

                result_replace_list = list()
                for index_replaces, index_copieds\
                        in zip(index_replaces_list_dict[attack_num],
                               index_copieds_list_dict[attack_num]):

                    attacked_list = replace_attack(modlist,
                                                   index_replaces,
                                                   index_copieds)

                    try:
                        # detection and calculation of precision
                        bin_similarity = detection_precision(attacked_list)
                        result_replace_list.append(bin_similarity)

                    except IndexError:
                        data = '0' * water_len
                        bin_similarity = (sum([w == d
                                            for w, d in zip(watermark_bin,
                                                            data)])
                                          / water_len
                                          * 100)

                        result_replace_list.append(bin_similarity)

                    sys.stdout.write('#')
                    sys.stdout.flush()

                result_replace_dict[attack_rate] = result_replace_list
            result_dict[attack] = result_replace_dict

        elif attack == 'collusion':
            for i in range(len(modlist)):
                continue

    with open(RESULT_PICKLE, 'wb') as f:
        pickle.dump(result_dict, f)
    with open('result/check.pkl', 'wb') as f:
        pickle.dump(total_len, f)
