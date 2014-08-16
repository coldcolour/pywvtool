#!/usr/local/bin/python
#encoding:utf8
'''
WordFilter interface and some build-in classes.
'''
class WordFilter(object):
    def __init__(self, params):
        pass

    def filter(self, token):
        raise NotImplementedError

class DummyWordFilter(WordFilter):
    def filter(self, token):
        '''return empty string if filtered'''
        return token

class StopWordFilter(WordFilter):
    pass
