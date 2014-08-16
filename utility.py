#!/usr/local/bin/python
#encoding:utf8
'''
Utility functions for all components.
'''

def check_required_params(keys, params):
    '''check required keys'''
    for key in keys:
        if key not in params:
            raise KeyError, "required arguemnt `%s' missing" % key

def param_adapter(param_string):
    '''
    Parse input parameter string into a dict.
    Input format: a) {a:x, b:y} b) a=x&b=y
    '''
    if not param_string:
        return {}

    if param_string.startswith("{"):
        return dict(eval(param_string))
    else:
        d = {}
        for part in param_string.split('&'):
            subpart = part.split('=')
            if len(subpart) == 2:
                k, v = subpart
                d[k] = v
        return d
