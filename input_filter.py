#!/usr/local/bin/python
#encoding:utf8
'''
InputFilter interface and some build-in classes.
'''

class InputFilter(object):
    def __init__(self, params):
        pass

    def filter(self, stream):
        raise NotImplementedError

class DummyInputFilter(InputFilter):
    def filter(self, stream):
        return stream

def _strip_tags(s):
    intag = [False]

    def chk(c):
        if intag[0]:
            intag[0] = (c != '&gt;')
            return False
        elif c == '&lt;':
            intag[0] = True
            return False
        return True

    return ''.join(c for c in s if chk(c))

class TagRemoverFilter(InputFilter):
    '''remove html/xml tags'''
    def filter(self, stream):
        try:
            from ab.util.BeautifulSoup import BeautifulSoup
            def visible(element): 
                import re
                if element.parent.name in ['style', 'script', '[document]', 'head']: 
                    return False 
                elif re.match('<!--.*-->', str(element)): 
                    return False 
                else:
                    return True 
            soup = BeautifulSoup(stream)
            texts = soup.findAll(text=True)
            visible_texts = filter(visible, texts)
            return ''.join(visible_texts)
        except ImportError:
            return _strip_tags(stream)

class TagWeightingFilter(InputFilter):
    def filter(self, stream):
        pass

