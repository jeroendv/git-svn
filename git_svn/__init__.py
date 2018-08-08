# -*- coding: utf-8 -*-
import pkg_resources

try:
    __version__ = pkg_resources.get_distribution(__name__).version
except:
    __version__ = 'unknown'


from functools import wraps
from git_svn.debug import DebugLog

def logFunctionScope(f):
    @wraps(f)
    def wrap(*args, **kw):
        with DebugLog.scopedPush("Enter: " +f.__name__):
            result = f(*args, **kw)
            return result
        
    return wrap
