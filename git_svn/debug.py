from __future__ import print_function

class DebugLogScopedPush:
    def __init__(self, msg = None):
        self.msg = msg

    def __enter__(self):
        if(self.msg is not None):
            DebugLog.print(self.msg)
            
        self.originalIndentLvl = DebugLog.indentLvl
        DebugLog.push()
    
    def __exit__(self, type, value, traceback):
        DebugLog.pop()
        assert(DebugLog.indentLvl == self.originalIndentLvl)


class DebugLog:
    """An indentation aware debug log stream"""

    indentLvl = 0
    enabled = False

    @staticmethod
    def print(msg):
        # skip debug messages if debug mode is not enabled!
        if DebugLog.enabled:
            print("|  "*DebugLog.indentLvl + msg)

    @staticmethod
    def push():
        DebugLog.indentLvl += 1
        return DebugLog.indentLvl

    @staticmethod
    def scopedPush(msg = None):
        return DebugLogScopedPush(msg)

    @staticmethod
    def pop():
        newIndentLvl = DebugLog.indentLvl - 1

        # indentLvl can't become negative
        if newIndentLvl < 0:
            newIndentLvl = 0
        
        DebugLog.indentLvl = newIndentLvl
        return DebugLog.indentLvl