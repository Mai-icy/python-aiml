"""
This file contains assorted general utility functions used by other
modules in the PyAIML package.
"""
import re


def sentences(s):
    """将字符串s分割成一个句子列表。"""
    if not isinstance(s, str):
        raise TypeError("s must be a string")
    pattern = re.compile(r'[.?!？！。]')
    sentence_list = [i.strip() for i in pattern.split(s) if i]
    return sentence_list

