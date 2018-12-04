#! usr/bin/env python
# -*- coding: utf-8 -*-

import api
from watermark import detector
import consts

########### config ############

ORIGIN_FILE = consts.ORIGIN_FILE
MODIFIED_FILE = consts.MODIFIED_FILE
METHOD = consts.METHOD
ATTR_LIST = consts.ATTR_LIST
SENSITIVE = consts.SENSITIVE
GROUP_BY_ATTR = consts.GROUP_BY_ATTR
WATER_LEN = consts.WATER_LEN
MAX_BIN = consts.MAX_BIN

########### initial ############
_, origin_list = api.parsed_list(ORIGIN_FILE, header=True)
_, modified_list = api.parsed_list(MODIFIED_FILE, header=True)

# GROUP_BY_ATTRの番地
group_by = [ATTR_LIST.index(attr) for attr in GROUP_BY_ATTR]

########### detection ############
detected_bin = detector(origin_list, modified_list, group_by,
                        ATTR_LIST, WATER_LEN, METHOD)

print(detected_bin)
