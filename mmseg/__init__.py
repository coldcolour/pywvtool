#encoding:utf8
import os
from _mmseg import Dictionary as _Dictionary, Token, Algorithm
import _mmseg as mmseg

class Dictionary(_Dictionary):
    dictionaries = (
        ('chars', os.path.join(os.path.dirname(__file__), 'data', 'chars.dic')),
        ('words', os.path.join(os.path.dirname(__file__), 'data', 'words.dic')),
    )

    @staticmethod
    def load_dictionaries():
        for t, d in Dictionary.dictionaries:
            if t == 'chars':
                if not Dictionary.load_chars(d):
                    raise IOError("Cannot open '%s'" % d)
            elif t == 'words':
                if not Dictionary.load_words(d):
                    raise IOError("Cannot open '%s'" % d)

dict_load_defaults = Dictionary.load_dictionaries
dict_load_defaults()
 
def seg_txt(text):
    if type(text) is str:
        algor = mmseg.Algorithm(text)
        for tok in algor:
            yield tok.text
    else:
        yield ""

if __name__ == "__main__":
    text = """　六大门派围攻光明顶的时候被周芷若的倚天剑刺了一下（重伤，周手下留情，另张喜欢上周，没夺倚天被偷袭）
    """
    from collections import defaultdict
    word_count = defaultdict(int)
    for word in seg_txt(text):
        print word,
