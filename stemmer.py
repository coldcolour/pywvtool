#!/usr/local/bin/python
#encoding:utf8
'''
Stemmer interface and some build-in classes.
'''
class Stemmer(object):
    def __init__(self, params):
        pass

    def stem(self, token):
        raise NotImplementedError

class DummyStemmer(Stemmer):
    def stem(self, token):
        return token

class PorterStemmer(Stemmer):
    def stem(self, token):
        raise NotImplementedError
