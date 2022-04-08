"""
This class implements the AIML pattern-matching algorithm described
by Dr. Richard Wallace at the following site:
http://www.alicebot.org/documentation/matching.html
英文的处理方式就是按照单词分裂开，用单词树的方式储存各种回复方式
中文的处理方式就是把句子每个字分开，用不到分词
todo：如果使用字典构建节点树会很庞大，原来的代码利用字典实现，可以自己构建合适的类型
"""

from __future__ import print_function

from LangSupport import splitChinese
import marshal
import pprint
import re

from .constants import *


class PatternMgr:
    # 特殊的类型，在节点数的映射中充当key，其实可以搞个枚举类
    _UNDERSCORE = 0
    _STAR = 1
    _TEMPLATE = 2
    _THAT = 3
    _TOPIC = 4
    _BOT_NAME = 5

    def __init__(self):
        self._root = {}
        self._templateCount = 0
        self._botName = u"Nameless"
        punctuation = r"""`~!@#$%^&*()-_=+[{]}\|;:'",<.>/?，。！？"""
        self._puncStripRE = re.compile("[" + re.escape(punctuation) + "]")
        self._whitespaceRE = re.compile(r"\s+", re.UNICODE)

    def numTemplates(self):
        """返回当前存储的模板数量。"""
        return self._templateCount

    def setBotName(self, name):
        """
        设置bot的名称, 用于匹配模式中的标记 <bot name="name">.
        名称必须是一个单一的单词
        """
        # 将多个单词的名称折叠成一个单词
        self._botName = unicode(' '.join(splitChinese(name)))

    def dump(self):
        """打印所有学习过的模式，以便调试"""
        pprint.pprint(self._root)

    def save(self, filename):
        """将当前模式转储到指定的文件.  并在之后使用restore()恢复。"""
        try:
            outFile = open(filename, "wb")
            marshal.dump(self._templateCount, outFile)
            marshal.dump(self._botName, outFile)
            marshal.dump(self._root, outFile)
            outFile.close()
        except Exception as e:
            print(f"Error saving PatternMgr to file {filename}:")
            raise

    def restore(self, filename):
        """恢复原来的文件，见save()成员函数"""
        try:
            inFile = open(filename, "rb")
            self._templateCount = marshal.load(inFile)
            self._botName = marshal.load(inFile)
            self._root = marshal.load(inFile)
            inFile.close()
        except Exception as e:
            print("Error restoring PatternMgr from file %s:" % filename)
            raise

    def add(self, data, template):
        """
        data是[pattern/that/topic]
        添加模式标签，数据结构是节点树
        """
        pattern, that, topic = data
        # TODO: make sure words contains only legal characters
        # (alphanumerics,*,_)
        # 通过节点树导航到模板的位置，必要时添加节点。



        node = self._root
        for word in splitChinese(pattern):
            key = word
            if key == u"_":
                key = self._UNDERSCORE
            elif key == u"*":
                key = self._STAR
            elif key == u"BOT_NAME":
                key = self._BOT_NAME
            if key not in node:
                node[key] = {}
            node = node[key]

        # 如果包含一个非空的that参数，则添加它，key为枚举数据中
        if that:
            if self._THAT not in node:
                node[self._THAT] = {}
            node = node[self._THAT]
            for word in splitChinese(that):
                key = word
                if key == u"_":
                    key = self._UNDERSCORE
                elif key == u"*":
                    key = self._STAR
                if key not in node:
                    node[key] = {}
                node = node[key]

        # 同理如果topic非空，也去添加
        if topic:
            if self._TOPIC not in node:
                node[self._TOPIC] = {}
            node = node[self._TOPIC]
            for word in splitChinese(topic):
                key = word
                if key == u"_":
                    key = self._UNDERSCORE
                elif key == u"*":
                    key = self._STAR
                if key not in node:
                    node[key] = {}
                node = node[key]

        # add the template.
        if self._TEMPLATE not in node:
            self._templateCount += 1
        node[self._TEMPLATE] = template

    def match(self, pattern, that, topic):
        """
        Return the template which is the closest match to pattern. The
        'that' parameter contains the bot's previous response. The 'topic'
        parameter contains the current topic of conversation.

        返回与pattern最匹配的模板。“that”参数包含机器人之前的响应。“topic”参数包含当前会话的topic。

        Returns None if no template is found.

        英文的处理就是所有字母大写，并且以空格为界，进行直接的分词
        """
        if len(pattern) == 0:
            return None
        # 切片输入。删除所有标点符号并将文本转换为全部大写。
        input_ = pattern.upper()
        input_ = re.sub(self._puncStripRE, " ", input_)
        if that.strip() == u"":
            that = u"ULTRABOGUSDUMMYTHAT"  # 'that' must never be empty
        thatInput = that.upper()
        thatInput = re.sub(self._puncStripRE, " ", thatInput)
        thatInput = re.sub(self._whitespaceRE, " ", thatInput)
        if topic.strip() == u"":
            topic = u"ULTRABOGUSDUMMYTOPIC"  # 'topic' must never be empty
        topicInput = topic.upper()
        topicInput = re.sub(self._puncStripRE, " ", topicInput)

        # 将输入传递给递归调用
        patMatch, template = self._match(splitChinese(input_), splitChinese(thatInput), splitChinese(topicInput), self._root)
        return template

    def star(self, starType, pattern, that, topic, index):
        """Returns a string, the portion of pattern that was matched by a *.
            返回模式中与*匹配的字符串
        The 'starType' parameter specifies which type of star to find.
        Legal values are:
         - 'star': matches a star in the main pattern.
         - 'thatstar': matches a star in the that pattern.
         - 'topicstar': matches a star in the topic pattern.
        """
        # 切片输入。删除所有标点符号并将文本转换为全部大写。（当然这是关于英文的处理）
        input_ = pattern.upper()
        input_ = re.sub(self._puncStripRE, " ", input_)
        input_ = re.sub(self._whitespaceRE, " ", input_)
        if that.strip() == u"":
            that = u"ULTRABOGUSDUMMYTHAT"  # 'that' must never be empty
        thatInput = that.upper()
        thatInput = re.sub(self._puncStripRE, " ", thatInput)
        thatInput = re.sub(self._whitespaceRE, " ", thatInput)
        if topic.strip() == u"":
            topic = u"ULTRABOGUSDUMMYTOPIC"  # 'topic' must never be empty
        topicInput = topic.upper()
        topicInput = re.sub(self._puncStripRE, " ", topicInput)
        topicInput = re.sub(self._whitespaceRE, " ", topicInput)

        # Pass the input off to the recursive pattern-matcher
        patMatch, template = self._match(
            splitChinese(input_), splitChinese(thatInput), splitChinese(topicInput), self._root)
        if template is None:
            return ""

        # Extract the appropriate portion of the pattern, based on the
        # starType argument.
        words = None
        if starType == 'star':
            patMatch = patMatch[:patMatch.index(self._THAT)]
            words = splitChinese(input_)
        elif starType == 'thatstar':
            patMatch = patMatch[patMatch.index(
                self._THAT) + 1: patMatch.index(self._TOPIC)]
            words = splitChinese(thatInput)
        elif starType == 'topicstar':
            patMatch = patMatch[patMatch.index(self._TOPIC) + 1:]
            words = splitChinese(topicInput)
        else:
            # unknown value
            raise ValueError(
                "starType must be in ['star', 'thatstar', 'topicstar']")

        # 将输入字符串与匹配的模式逐字比较。
        # At the end of this loop, if foundTheRightStar is true, start and
        # end will contain the start and end indices (in "words") of
        # the substring that the desired star matched.
        # 在循环结束时，如果foundTheRightStar值为true, start和end将包含所需星号匹配的子字符串的起始和结束索引(以“words”表示)。
        foundTheRightStar = False
        start = end = j = numStars = k = 0
        for i in range(len(words)):
            # This condition is true after processing a star
            # that ISN'T the one we're looking for.
            if i < k:
                continue
            # If we're reached the end of the pattern, we're done.
            if j == len(patMatch):
                break
            if not foundTheRightStar:
                if patMatch[j] in [
                        self._STAR, self._UNDERSCORE]:  # we got a star
                    numStars += 1
                    if numStars == index:
                        # This is the star we care about.
                        foundTheRightStar = True
                    start = i
                    # Iterate through the rest of the string.
                    for k in range(i, len(words)):
                        # If the star is at the end of the pattern,
                        # we know exactly where it ends.
                        if j + 1 == len(patMatch):
                            end = len(words)
                            break
                        # If the words have started matching the
                        # pattern again, the star has ended.
                        if patMatch[j + 1] == words[k]:
                            end = k - 1
                            i = k
                            break
                # If we just finished processing the star we cared
                # about, we exit the loop early.
                if foundTheRightStar:
                    break
            # Move to the next element of the pattern.
            j += 1

        # extract the star words from the original, unmutilated input.
        if foundTheRightStar:
            # print( ' '.join(pattern.split()[start:end+1]) )
            if starType == 'star':
                return ' '.join(splitChinese(pattern)[start:end + 1])
            elif starType == 'thatstar':
                return ' '.join(splitChinese(that)[start:end + 1])
            elif starType == 'topicstar':
                return ' '.join(splitChinese(topic)[start:end + 1])
        else:
            return u""

    def _match(self, words, thatWords, topicWords, root):
        """Return a tuple (pat, tem) where pat is a list of nodes, starting
        at the root and leading to the matching pattern, and tem is the
        matched template.

        返回一个元组(pat, tem)，其中pat是开始的节点列表在根和引导匹配模式，tem是匹配的模板。
        """
        # base-case: 如果单词列表为空，则返回当前节点的template
        if len(words) == 0:
            # 回复为空
            pattern = []
            template = None
            if len(thatWords) > 0:
                # If thatWords isn't empty, recursively
                # pattern-match on the _THAT node with thatWords as words.
                try:
                    pattern, template = self._match(
                        thatWords, [], topicWords, root[self._THAT])
                    if pattern is not None:
                        pattern = [self._THAT] + pattern
                except KeyError:
                    pattern = []
                    template = None
            elif len(topicWords) > 0:
                # If thatWords is empty and topicWords isn't, recursively pattern
                # on the _TOPIC node with topicWords as words.
                try:
                    pattern, template = self._match(
                        topicWords, [], [], root[self._TOPIC])
                    if pattern is not None:
                        pattern = [self._TOPIC] + pattern
                except KeyError:
                    pattern = []
                    template = None
            if template is None:
                # we're totally out of input.  Grab the template at this node.
                pattern = []
                try:
                    template = root[self._TEMPLATE]
                except KeyError:
                    template = None
            return pattern, template

        first = words[0]
        suffix = words[1:]

        # 检查下划线。
        # Note: this is causing problems in the standard AIML set, and is currently disabled.
        # 这将导致标准AIML集中出现问题，目前已禁用。
        if self._UNDERSCORE in root:
            # Must include the case where suf is [] in order to handle the case
            # where a * or _ is at the end of the pattern.
            for j in range(len(suffix) + 1):
                suf = suffix[j:]
                pattern, template = self._match(
                    suf, thatWords, topicWords, root[self._UNDERSCORE])
                if template is not None:
                    newPattern = [self._UNDERSCORE] + pattern
                    return newPattern, template

        # Check first
        if first in root:
            pattern, template = self._match(suffix, thatWords, topicWords, root[first])
            if template is not None:
                newPattern = [first] + pattern
                return newPattern, template

        # check bot name
        if self._BOT_NAME in root and first == self._botName:
            pattern, template = self._match(
                suffix, thatWords, topicWords, root[self._BOT_NAME])
            if template is not None:
                newPattern = [first] + pattern
                return newPattern, template

        # check star
        if self._STAR in root:
            # Must include the case where suf is [] in order to handle the case
            # where a * or _ is at the end of the pattern.
            for j in range(len(suffix) + 1):
                suf = suffix[j:]
                pattern, template = self._match(
                    suf, thatWords, topicWords, root[self._STAR])
                if template is not None:
                    newPattern = [self._STAR] + pattern
                    return newPattern, template

        # 没有结果.
        return None, None
