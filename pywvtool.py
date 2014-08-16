#!/usr/local/bin/python
#encoding:utf8
'''
PyWVTool - Python Word Vector Tool, used to convert text files into feature vectors.
'''
from __future__ import with_statement
import sys
import os
from math import sqrt, log
import codecs

class PythonWVTool(object):
    '''Python word vector tool'''
    def __init__(self, taskname, output_folder, loader, input_filter, 
            tokenizer, word_filter, stemmer, user_dict, encoding='utf8'):
        # default config
        self.mindf = 2 # df < mindf will be removed
        self.maxdf = 1000000 # df > maxdf will be removed
        self.default_encoding = encoding

        # parameters
        self.taskname = taskname
        self.output_folder = output_folder
        self.loader = loader
        self.input_filter = input_filter
        self.tokenizer = tokenizer
        self.word_filter = word_filter
        self.stemmer = stemmer
        if user_dict:
            self.lexicon = {}
            with codecs.open(user_dict, 'r', encoding=self.default_encoding, errors='strict') as fdict:
                for index, line in enumerate(fdict):
                    if isinstance(line, str):
                        line = line.decode(self.default_encoding, 'strict')
                    self.lexicon[line.strip()] = index
            self.user_dict = True
        else:
            self.lexicon = {} # word -> id
            self.last_tokenid = 0
            self.user_dict = False

        # statistics
        self.task_stat = {'document_count':0, 'word_count':0}
        self.doc_stat = {'id':-1, 'uri':'', 'word_freq':{}}

    def _filename(self, key):
        '''return full path of specified file'''
        return os.path.join(self.output_folder, "%s.%s" % (self.taskname, key))

    def index_corpus(self):
        '''
        Index the corpus, produce .ii, .tf, .corpus, .docinfo, .dic, etc.
        '''
        if not os.path.exists(self.output_folder):
            os.mkdir(self.output_folder)

        ftf = open(self._filename('tf'), 'w')
        fdocinfo = open(self._filename('docinfo'), 'w')
        ftmp = open(self._filename('tmp'), 'w')

        self.loader.open()
        docid = 0
        for item in self.loader.items():
            uri, content = item
            self.doc_stat['id'] = docid
            self.doc_stat['uri'] = uri
            self.doc_stat['word_freq'] = {}
            #import pdb; pdb.set_trace()
            for token in self.tokenizer.tokenize(self.input_filter.filter(content)):
                token = self.stemmer.stem(self.word_filter.filter(token))
                if not token:
                    continue
                if self.user_dict:
                    tokenid = self._find_token(token)
                    if tokenid == -1:
                        continue # out of user dict
                else:
                    tokenid = self._find_update_token(token)
                # update word statistics
                self._update_word(tokenid)
            self._update_doc(ftf, fdocinfo, ftmp)
            docid += 1
        self.loader.close()

        # close handlers
        ftf.close()
        ftmp.close()
        fdocinfo.close()
        # create inverted index from .tmp
        token_map = self._inverted_index()
        # use new tokenid to output .dic/.tf/.corpus
        self._update_task(token_map)

    def create_vector(self, weighting):
        '''create feature vector'''
        if weighting not in ['TF', 'TFIDF']:
            raise NotImplementedError, "Not implemented weighting method %s" % weighting
        if weighting == 'TF':
            self._tf()
        elif weighting == 'TFIDF':
            self._tfidf()
        else:
            pass

    def _tf(self):
        '''normalized term frequency vector'''
        path_tf = self._filename('tf')
        path_output = self._filename('wv')
        fd_output = open(path_output, 'w')
        with open(path_tf, 'r') as f:
            for line in f:
                line = line.strip()
                parts = line.split()
                if len(parts) < 2:
                    continue
                docid = int(parts[0])
                wordfreq = {}
                length = 0.0
                for part in parts[1:]:
                    subparts = part.split(':')
                    if len(subparts) != 2:
                        continue
                    wordfreq[int(subparts[0])] = int(subparts[1])
                    length += float(subparts[1]) * float(subparts[1])
                length = sqrt(length)
                sorted_items = wordfreq.items()
                sorted_items.sort(key=lambda x:x[0])
                fd_output.write("%d %s\n" % (docid, 
                    ' '.join(["%d:%f" % (k, v/length) for (k, v) in sorted_items])))
        fd_output.close()

    def _tfidf(self):
        '''normalized td*idf weighting vector'''
        path_tf = self._filename('tf')
        path_ii = self._filename('ii')
        path_corpus = self._filename('corpus')
        path_output = self._filename('wv')

        # read doc_count
        with open(path_corpus) as f:
            lines = f.readlines()
            for line in lines:
                parts = line.strip().split('=')
                if len(parts) == 2 and parts[0] == 'document_count':
                    doc_count = int(parts[1])
        # read df
        token2df = {}
        with open(path_ii) as f:
            for line in f:
                parts = line.strip().split(',')
                token2df[int(parts[0])] = int(parts[1])

        fd_output = open(path_output, 'w')
        #import pdb; pdb.set_trace()
        with open(path_tf, 'r') as f:
            for line in f:
                line = line.strip()
                parts = line.split()
                if len(parts) < 2:
                    continue
                docid = int(parts[0])
                wordfreq = {}
                wordtfidf = {}
                for part in parts[1:]:
                    subparts = part.split(':')
                    if len(subparts) != 2:
                        continue
                    wordfreq[int(subparts[0])] = int(subparts[1])
                word_count = float(sum(wordfreq.values()))
                length = 0.0
                for word in wordfreq:
                    if word not in token2df:
                        continue # some word is pruned in all document
                    wordtfidf[word] = wordfreq[word] / word_count * \
                            log(float(doc_count) / token2df[word])
                    length += wordtfidf[word] * wordtfidf[word]
                length = sqrt(length)
                sorted_items = wordtfidf.items()
                sorted_items.sort(key=lambda x:x[0])
                fd_output.write("%d %s\n" % (docid, 
                    ' '.join(["%d:%f" % (k, v/length) for (k, v) in sorted_items if v > 1E-5])))
        fd_output.close()

    def _inverted_index(self):
        '''create inverted index from .tmp file'''
        filename_sort = self._filename('tmp') + ".sort"
        cmd = "sort -t, -n -k1,1 -k2,2 -u %s -o %s" \
                % (self._filename('tmp'), filename_sort)
        os.system(cmd)
        lasttid = -1
        docbin = []
        token_map = {} # old tokenid -> new tokenid
        new_token_id = 0
        fdii = open(self._filename('ii'), 'w')
        #import pdb; pdb.set_trace()
        with open(filename_sort) as fd:
            for line in fd:
                tid, did = line.strip().split(',')
                tid = int(tid)
                did = int(did)
                if lasttid != -1 and tid != lasttid:
                    df = len(docbin)
                    if self.user_dict or df >= self.mindf and df <= self.maxdf:
                        # when use customized dictionary, token will not be filtered by df
                        if lasttid not in token_map:
                            if not self.user_dict:
                                token_map[lasttid] = new_token_id
                                new_token_id += 1
                            else:
                                token_map[lasttid] = lasttid
                        docbin.sort()
                        fdii.write("%s,%d,%s\n" % (token_map[lasttid], len(docbin), ','.join(["%d" % docid for docid in docbin])))
                        docbin = []
                    else:
                        docbin = []
                docbin.append(did)
                lasttid = tid
            else:
                if docbin:
                    df = len(docbin)
                    if self.user_dict or df >= self.mindf and df <= self.maxdf:
                        # when use customized dictionary, token will not be filtered by df
                        if lasttid not in token_map:
                            if not self.user_dict:
                                token_map[lasttid] = new_token_id
                                new_token_id += 1
                            else:
                                token_map[lasttid] = lasttid
                        docbin.sort()
                        fdii.write("%s,%d,%s\n" % (token_map[lasttid], len(docbin), ','.join(["%d" % did for did in docbin])))
        fdii.close()
        os.remove(self._filename('tmp'))
        os.remove(filename_sort)
        #print len(self.lexicon), len(token_map)
        return token_map

    def _find_token(self, token):
        '''Use user dict to find id of token'''
        return self.lexicon.get(token, -1)

    def _find_update_token(self, token):
        '''find id for a token, insert new if not found'''
        if token in self.lexicon:
            return self.lexicon[token]
        else:
            self.lexicon[token] = self.last_tokenid
            self.last_tokenid += 1
            return self.last_tokenid - 1

    def _update_word(self, tokenid):
        '''update word related stat'''
        if tokenid in self.doc_stat['word_freq']:
            self.doc_stat['word_freq'][tokenid] += 1
        else:
            self.doc_stat['word_freq'][tokenid] = 1

    def _update_doc(self, ftf, fdocinfo, ftmp):
        '''update when a doc is just indexed'''
        self.task_stat['document_count'] += 1
        ftf.write("%d %s\n" % (self.doc_stat['id'], 
            " ".join(["%s:%d" % (k, v) for (k, v) in self.doc_stat['word_freq'].items()])))
        ftf.flush()
        fdocinfo.write("%d,%s\n" % (self.doc_stat['id'], self.doc_stat['uri']))
        fdocinfo.flush()
        ftmp.write('\n'.join(["%d,%d" % (k, self.doc_stat['id']) 
            for k in self.doc_stat['word_freq']]))
        if self.doc_stat['word_freq']:
            ftmp.write('\n')
        ftmp.flush()

    def _dump_dic(self, token_map):
        '''dump .dic file'''
        if self.user_dict or len(token_map) == len(self.lexicon):
            return

        items = [(token_map[oid], token) for (token, oid) in self.lexicon.items() if oid in token_map]
        items.sort() # sort by id, token
        with open(self._filename("dic"), "w") as fdic:
            fdic.write("%s\n" % ("\n".join(
                ["%s" %(item[1].encode(self.default_encoding, 'ignore')) for item in items])))

    def _rewrite_tf(self, token_map):
        '''rewrite the tf file using the token id mapping'''
        if len(token_map) == len(self.lexicon):
            return

        self.task_stat['word_count'] = 0
        fnnew = self._filename('tf') + ".new"
        fnew = open(fnnew, 'w')
        fnold = self._filename('tf')
        with open(fnold) as foldtf:
            for line in foldtf: # docid tokenid:tf tokenid:tf ...
                parts = line.strip().split()
                docid = int(parts[0])
                vector = [] # (newtid, tf)
                for part in parts[1:]:
                    subparts = part.split(':')
                    tid = int(subparts[0])
                    tf = int(subparts[1])
                    if tid in token_map:
                        vector.append((token_map[tid], tf))
                vector.sort()
                fnew.write("%d %s\n" % (docid, " ".join(["%d:%d" %(k, v) for (k, v) in vector])))
                self.task_stat['word_count'] += sum([item[1] for item in vector])
        fnew.close()
        os.remove(fnold)
        os.rename(fnnew, fnold)

    def _update_task(self, token_map):
        ''' Write .dic, .corpus; rewrite .tf if needed.  '''
        self._dump_dic(token_map)
        self._rewrite_tf(token_map)
        self._dump_corpus()

    def _dump_corpus(self):
        '''dump .corpus file'''
        with open(self._filename('corpus'), 'w') as fcorpus:
            fcorpus.write("%s\n" 
                    % ("\n".join("%s=%s" % (k,v) for (k,v) in self.task_stat.items())))

def getopts():
    '''parse options'''
    from optparse import OptionParser
    usage = "Python word vector tool"
    parser = OptionParser(usage=usage)
    parser.add_option("-t", "--taskname", dest="taskname", default="", 
            help="name of task") # required
    parser.add_option("-o", "--output-folder", dest="output_folder", default="", 
            help="output folder") # required
    parser.add_option("-e", "--encoding", dest="encoding", default="utf8", 
            help="default system encoding, utf8 by default")
    parser.add_option("", "--loader", dest="loader", default="", 
            help="loader's name")
    parser.add_option("", "--loader-op", dest="loader_op", default="", 
            help="loader's option") 
    parser.add_option("", "--input-filter", dest="input_filter", default="DummyInputFilter", 
            help="InputFilter's name, default DummyInputFilter")
    parser.add_option("", "--input-filter-op", dest="input_filter_op", default="", 
            help="InputFilter's option, default empty, if given, follow \"a=x&b=y&c=z\" or dict format") 
    parser.add_option("", "--tokenizer", dest="tokenizer", default="CharTokenizer",
            help="Tokenizer's name, default CharTokenizer")
    parser.add_option("", "--tokenizer-op", dest="tokenizer_op", default="",
            help="Tokenizer's option, default empty")
    parser.add_option("", "--word-filter", dest="word_filter", default="DummyWordFilter",
            help="WordFilter's name, default DummyWordFilter")
    parser.add_option("", "--word-filter-op", dest="word_filter_op", default="",
            help="WordFilter's option, default empty")
    parser.add_option("", "--stemmer", dest="stemmer", default="DummyStemmer",
            help="Stemmer's name, default DummyStemmer")
    parser.add_option("", "--stemmer-op", dest="stemmer_op", default="",
            help="Stemmer's option, default empty")
    parser.add_option("-w", "--weighting", dest="weighting", default="TFIDF",
            help="Weighting method, default TFIDF")
    parser.add_option("-u", "--user-dict", dest="user_dict", default="",
            help="path to user dict file, format id,term")
    parser.add_option("-p", "--psyco", action='store_true', 
                    dest="psyco", default=False,
                    help="to enable psyco")
    options = parser.parse_args()[0]
    if not (options.taskname and options.output_folder and options.loader and options.loader_op):
        print "Syntax error, please type -h to see usage."
        sys.exit(-1)
    if options.psyco:
        import psyco
        psyco.full()
    return options

def main():
    '''main entry'''
    from utility import param_adapter
    options = getopts()

    # construct components from options
    taskname = options.taskname
    output_folder = options.output_folder
    weighting = options.weighting.upper()
    user_dict = options.user_dict
    encoding = options.encoding
    if options.loader in globals():
        loader = globals()[options.loader](param_adapter(options.loader_op))
    else:
        module = __import__('loader') # default module
        loader = getattr(module, options.loader)(param_adapter(options.loader_op))
    if options.input_filter in globals():
        input_filter = globals()[options.input_filter](param_adapter(options.input_filter_op))
    else:
        module = __import__('input_filter') # default module
        input_filter = getattr(module, options.input_filter)(param_adapter(options.input_filter_op))
    if options.tokenizer in globals():
        tokenizer = globals()[options.tokenizer](param_adapter(options.tokenizer_op))
    else:
        module = __import__('tokenizer') # default module
        tokenizer = getattr(module, options.tokenizer)(param_adapter(options.tokenizer_op))
    if options.word_filter in globals():
        word_filter = globals()[options.word_filter](param_adapter(options.word_filter_op))
    else:
        module = __import__('word_filter') # default module
        word_filter = getattr(module, options.word_filter)(param_adapter(options.word_filter_op))
    if options.stemmer in globals():
        stemmer = globals()[options.stemmer](param_adapter(options.stemmer_op))
    else:
        module = __import__('stemmer') # default module
        stemmer = getattr(module, options.stemmer)(param_adapter(options.stemmer_op))

    pywvtool = PythonWVTool(taskname, output_folder, loader, input_filter, 
            tokenizer, word_filter, stemmer, user_dict, encoding)
    pywvtool.index_corpus()
    pywvtool.create_vector(weighting)

if __name__ == "__main__":
    main()
