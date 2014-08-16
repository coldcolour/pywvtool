#!/usr/local/bin/python
#encoding:gbk
'''
Tokenizer interface and some default classes.
'''
from utility import check_required_params

class Tokenizer(object):
    def __init__(self, params=None):
        pass

    def tokenize(self, stream):
        raise NotImplementedError

class ChunkTokenizer(Tokenizer):
    '''Split input stream into pieces delimitered by punctions, i.e. sub-sentence level'''
    def tokenize(self, stream):
        p = 0 
        q = 0
        size = len(stream)
        while True:
            # skip non alnum
            while p < size and not stream[p].isalnum():
                p += 1

            if p == size:
                break

            # read until a non-alnum
            q = p
            while p < size and stream[p].isalnum():
                p += 1
            chunk = stream[q:p]
            yield chunk

class NGramTokenizer(Tokenizer):
    '''Emit n-grams based on chunks'''
    def __init__(self, params):
        super(NGramTokenizer, self).__init__(params)
        check_required_params(['n'], params)
        try:
            self.n = int(params['n'])
            assert(self.n > 0)
        except ValueError:
            self.n = 1
        self._imp_tokenizer = ChunkTokenizer()

    def tokenize(self, stream):
        for chunk in self._imp_tokenizer.tokenize(stream):
            size = len(chunk)
            for i in range(size-self.n+1):
                yield chunk[i:i+self.n]

class CharTokenizer(NGramTokenizer):
    def __init__(self, params):
        super(CharTokenizer, self).__init__({'n':1})

class ABTokenizer(Tokenizer):
    ABWDE_HOME = "ABWDE_HOME"

    def __init__(self, params=None):
        from ab.util.abwords import ABWORDS
        import os
        super(ABTokenizer, self).__init__(params)
        # user dict from params
        dictList = []
        #dictList.append(os.environ[self.ABWDE_HOME] + '/dict/Aibang_basicDict.txt')
        #dictList.append(os.environ[self.ABWDE_HOME] + '/dict/Aibang_groupDict.txt')
        dictList.append(os.environ[self.ABWDE_HOME] + '/dict/sougou.dict')
        self._wordparser = ABWORDS(dictList)
        self._imp_tokenizer = ChunkTokenizer()

    def tokenize(self, stream):
        gbk_stream = stream.encode('gbk', 'ignore')
        for chunk in self._imp_tokenizer.tokenize(stream):
            words = self._wordparser.seg_words(chunk.encode('gbk', 'ignore'))
            for word in words:
                yield word.decode('gbk', 'ignore')

class MMSegTokenizer(Tokenizer):
    def __init__(self, params=None):
        super(MMSegTokenizer, self).__init__(params)
        self._imp_tokenizer = ChunkTokenizer()

    def tokenize(self, stream):
        import mmseg
        for chunk in self._imp_tokenizer.tokenize(stream):
            r = mmseg.seg_txt(chunk.encode('utf8', 'ignore'))
            for word in r:
                yield word.decode('utf8', 'ignore')

if __name__ == "__main__":
    #import pdb; pdb.set_trace()
    s = "《通知》要求：一是自2010年10月1日起，所有经出厂检验合格的轿车产品，办理注册登记前，都无需再进行机动车安全技术检验；二是经工业和信息化部批准、具备生产一致性保证能力的企业生产的其他小型、微型载客汽车和两轮摩托车，无需进行机动车安全技术检验。"
    #a = ABTokenizer()
    #for word in a.tokenize(s.decode('gbk', 'ignore')):
    #    print word.encode('gbk', 'ignore')
    a = MMSegTokenizer()
    for word in a.tokenize(s.decode('utf8', 'ignore')):
        print word.encode('utf8', 'ignore')
