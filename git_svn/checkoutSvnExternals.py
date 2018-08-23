from __future__ import print_function
import sys
import os
from git_svn.debug import *
import argparse
from git_svn.git import *
from git_svn.svn import *

from concurrent.futures import ThreadPoolExecutor

if sys.version_info < (3,5):
    print("Script is being run with a too old version of Python. Needs 3.5.")
    sys.exit(0)

args = []

def parse_cli_args():
    """parse the script input arguments"""
    parser = argparse.ArgumentParser(description=r"""checkout svn externals""")

    parser.add_argument("-v", "--verbose",
                    help="increase output verbosity",
                    action="store_true")

    parser.add_argument("-d", "--debug",
                    help="enable debug output",
                    action="store_true")
                   

    parser.add_argument("-N", "--dry-run",
                        help="Do not perform any actions, only simulate them.",
                        action="store_true")

    args = parser.parse_args()



    # register custom exception handler
    h = ExceptionHandle(args.debug)
    sys.excepthook = h.exception_handler

    DebugLog.enabled = args.debug
    with DebugLogScopedPush("cli arguments:"):
        DebugLog.print(str(args))
    
    return args

def checkoutExternal(svnExternal):
    """
    checkout a single external
    """
    print(svnExternal.svnWCFolderPath + " : " + str(svnExternal))
            
    if not args.dry_run:
        checkoutSvnExternal(svnExternal)    


def main():
    args = parse_cli_args()

    if IsGitSvnRepo():    
        # if therws is a git-svn repo then lets assume it is the main Working copy
        # and git in favor of svn 
        externalDefinitions = GetSvnExternalsFromGitSvnBridge()
    elif IsSvnWc():
        # use svn WC info if available
        externalDefinitions = GetSvnExternalsFromLocalSvnWc()
    else:
        raise Exception("cwd is not a git-svn bridge nor an svn working copy")

    print("#externals: " + str(len(externalDefinitions)))

    # fetch all externals concurrently using multiple workers
    with ThreadPoolExecutor(max_workers=8) as e:
        e.map(checkoutExternal, externalDefinitions)
                       

    sys.exit(0)
