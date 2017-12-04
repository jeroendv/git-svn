import sys
import traceback
from git_svn.debug import *
import argparse

def parse_cli_args():
    """parse the script input arguments"""
    parser = argparse.ArgumentParser(description="create a git svn bridge repo in an svn working copy")

    parser.add_argument("-v", "--verbose",
                    help="increase output verbosity",
                    action="store_true")

    parser.add_argument("-d", "--debug",
                    help="enable debug output",
                    action="store_true")
                   

    parser.add_argument("-N", "--dry-run",
                        help="Do not perform any actions, only simulate them.")

    args = parser.parse_args()

    # register custom exception handler
    h = ExceptionHandle(args.debug)
    sys.excepthook = h.exception_handler

    with DebugLogScopedPush("cli arguments:"):
        DebugLog.print(str(args))
    
    return args


class ExceptionHandle:
    """Exception handler for this cli"""

    def __init__(self, debug):
        self.debug = debug

    def exception_handler(self, exception_type, exception, tb):
        # format python exception
        print(str(exception_type.__name__) + " : " + str(exception))

        # print stack trace in debug mode only
        if (self.debug):
            traceback.print_tb(tb)


def main():
    args = parse_cli_args()

    sys.exit(0)