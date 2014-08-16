#!/usr/local/bin/python
#encoding:utf8
'''
Loader interface and some build-in classes.
'''
from __future__ import with_statement
import os
import codecs
from utility import check_required_params

class Loader(object):
    '''Abstract Loader interface'''
    def open(self):
        '''open the source connection'''
        raise NotImplementedError

    def items(self):
        '''generator for the items'''
        raise NotImplementedError

    def close(self):
        '''close the connection'''
        raise NotImplementedError

class LocalFileLoader(Loader):
    '''loader that handles a single local file'''
    def __init__(self, params):
        super(LocalFileLoader, self).__init__()
        check_required_params(['src'], params)
        self._source = params['src']
        self._encoding = 'utf8' if 'encoding' not in params else params['encoding']
        self._fd = None
    
    def open(self):
        '''open the source connection'''
        try:
            self._fd = codecs.open(self._source, mode='r', encoding=self._encoding, errors='ignore')
        except IOError:
            if self._fd:
                self._fd.close()
                self._fd = None

    def items(self):
        '''generator for the items'''
        # only one item 
        if self._fd:
            yield self._source, self._fd.read() #.decode(self._encoding, 'ignore')

    def close(self):
        '''close the connection'''
        if self._fd:
            self._fd.close()

class LocalFilelistLoader(Loader):
    '''loader that handles a file with all files' paths in it '''
    def __init__(self, params):
        super(LocalFilelistLoader, self).__init__()
        check_required_params(['src'], params)
        self._source = params['src']
        self._encoding = 'utf8' if 'encoding' not in params else params['encoding']
        self._fd = None
    
    def open(self):
        '''open the source connection'''
        try:
            self._fd = codecs.open(self._source, mode='r', encoding=self._encoding, errors='ignore')
        except IOError:
            if self._fd:
                self._fd.close()
                self._fd = None

    def items(self):
        '''generator for the items'''
        if self._fd:
            for line in self._fd:
                line = line.strip()
                if not line or not os.path.exists(line):
                    continue
                else:
                    with codecs.open(line, mode='r', encoding=self._encoding, errors='ignore') as fditem:
                        yield line, fditem.read()

    def close(self):
        '''close the connection'''
        if self._fd:
            self._fd.close()

class LocalKVFileLoader(Loader):
    '''loader that handles a file with one document per line; doc key\ttxt'''
    def __init__(self, params):
        super(LocalKVFileLoader, self).__init__()
        check_required_params(['src'], params)
        self._source = params['src']
        self._encoding = 'utf8' if 'encoding' not in params else params['encoding']
        self._fd = None
    
    def open(self):
        '''open the source connection'''
        try:
            self._fd = codecs.open(self._source, mode='r', encoding=self._encoding, errors='ignore')
        except IOError:
            if self._fd:
                self._fd.close()
                self._fd = None

    def items(self):
        '''generator for the items'''
        if self._fd:
            for line in self._fd:
                line = line.strip()
                parts = line.split('\t')
                if not parts or len(parts) != 2:
                    continue
                else:
                    yield parts[0], parts[1]

    def close(self):
        '''close the connection'''
        if self._fd:
            self._fd.close()

class WebLoader(Loader):
    '''loader that handles a single web page represented by URL'''
    def __init__(self, params):
        super(WebLoader, self).__init__()
        check_required_params(['url'], params)
        self._url = params['url']
        self._encoding = 'utf8' if 'encoding' not in params else params['encoding']
        self._doc = None

    def open(self):
        from urllib import urlopen
        self._doc = urlopen(self._url)

    def items(self):
        if self._doc:
            content = self._doc.read()
            ucontent = ''
            try:
                ucontent = content.decode('utf8')
            except UnicodeError:
                try:
                    ucontent = content.decode('gb2312')
                except UnicodeError:
                    pass
            yield self._url, ucontent

    def close(self):
        self._doc = None

class TextLoader(Loader):
    '''loader that handles a text content'''
    def __init__(self, params):
        super(TextLoader, self).__init__()
        check_required_params(['txt'], params)
        self._text = params['txt']
        self._encoding = 'utf8' if 'encoding' not in params else params['encoding']
        self._content = None
    
    def open(self):
        '''open the source connection'''
        self._content = self._text.decode(self._encoding, 'ignore')

    def items(self):
        '''generator for the items'''
        # only one item 
        yield self._text, self._content #.decode(self._encoding, 'ignore')

    def close(self):
        '''close the connection'''
        self._content = None

if __name__ == "__main__":
    loader = WebLoader({'url':'http://tuan.aibang.com/beijing/'})
    #loader = WebLoader({'url':'http://www.baidu.com/'})
    loader.open()
    for item in loader.items():
        print item
    loader.close()

