# usr/bin/ python
# coding: utf-8

import fastText as ft
import numpy as np


def load_model(model_bin):
    return ft.load_model(model_bin)


def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
