"""这个模块实现了WordSub类，按照书《Python Cookbook》内容构建的
(3.14, "Replacing Multiple Patterns in a Single Pass" by Xavier Defrang).
参考：https://www.oreilly.com/library/view/python-cookbook/0596001673/ch03s15.html
Usage:
Use this class like a dictionary to add before/after pairs:
    > subber = TextSub()
    > subber["before"] = "after"
    > subber["begin"] = "end"
Use the sub() method to perform the substitution:
    > print( subber.sub("before we begin") )
    after we end
All matching is intelligently case-insensitive:
    > print( subber.sub("Before we BEGIN") )
    After we END
The 'before' words must be complete words -- no prefixes.
The following example illustrates this point:
    > subber["he"] = "she"
    > print( subber.sub("he says he'd like to help her") )
    she says she'd like to help her
Note that "he" and "he'd" were replaced, but "help" and "her" were
not.
"""

from __future__ import print_function

from collections import UserDict
import re
import string
try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser


class WordSub(UserDict):
    """一体化multiple-string-substitution类。"""

    def _wordToRegex(self, word):
        """将一个单词转换为匹配该单词的regex对象。"""
        if word != "" and word[0].isalpha() and word[-1].isalpha():
            return "\\b%s\\b" % re.escape(word)
        else:
            return r"\b%s\b" % re.escape(word)

    def _update_regex(self):
        """基于当前字典的键来构建重新对象。"""
        self._regex = re.compile("|".join(map(self._wordToRegex, self.keys())))
        self._regexIsDirty = False

    def __init__(self, defaults=None):
        """初始化对象，并用默认字典中的条目填充它。"""
        super(WordSub, self).__init__()
        if defaults is None:
            defaults = {}
        self._regex = None
        self._regexIsDirty = True
        for k, v in defaults.items():
            self[k] = v

    def __call__(self, match):
        """Handler invoked for each regex match."""
        return self[match.group(0)]

    def __setitem__(self, i, y):
        self._regexIsDirty = True
        # for each entry the user adds, we actually add three entrys:
        super(WordSub, self).__setitem__(i.lower(), y.lower())  # key = value
        super(WordSub, self).__setitem__(string.capwords(i), string.capwords(y))  # Key = Value
        super(WordSub, self).__setitem__(i.upper(), y.upper())  # KEY = VALUE

    def sub(self, text):
        """Translate text, returns the modified text."""
        if self._regexIsDirty:
            self._update_regex()
        return self._regex.sub(self, text)

