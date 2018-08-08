# -*- coding: utf-8 -*-
import pkg_resources

try:
    __version__ = pkg_resources.get_distribution(__name__).version
except:
    __version__ = 'unknown'


from functools import wraps
from git_svn.debug import DebugLog
from time import time

def logFunctionScope(f):
    @wraps(f)
    def wrap(*args, **kw):
        with DebugLog.scopedPush("Enter: " +f.__name__):
            result = f(*args, **kw)
            return result
        
    return wrap
	
def timeit(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        print('func:{} args:[{}, {}] took: {:2.4f} sec'.format(
            f.__name__
            , args
            , kw
            , te-ts))
        return result
    return wrap
