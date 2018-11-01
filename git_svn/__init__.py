# -*- coding: utf-8 -*-
import pkg_resources

try:
    __version__ = pkg_resources.get_distribution(__name__).version
except:
    __version__ = 'unknown'


from functools import wraps
from git_svn.debug import DebugLog
from time import time
	
def timeit(f):
    """function decorator to measure and log its execution time"""
    @wraps(f)
    def wrap(*args, **kw):
        with DebugLog.scopedPush("Enter func: " +f.__name__ + " args:[" + str(args) + ", " + str(kw) +"]"):
            ts = time()
            result = f(*args, **kw)
            te = time()
            DebugLog.print('Exit func:{} args:[{}, {}] took: {:2.4f} sec'.format(
                f.__name__
                , args
                , kw
                , te-ts))
            return result
    return wrap
