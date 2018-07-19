from __future__ import print_function
import sys
import traceback
import os

from git_svn.debug import *
from git_svn.git import *
from git_svn.svn import *

import argparse
import subprocess
from xml.etree import ElementTree as ET

if sys.version_info < (3,5):
    print("Script is being run with a too old version of Python. Needs 3.5.")
    sys.exit(0)

args = []

def parse_cli_args():
    """parse the script input arguments"""
    parser = argparse.ArgumentParser(description=r"""migrate svn ignore rules:

    1) ignore rules from svn itself, i.e. svn:ignore properties
    2) ignore .svn/ in git
    3) ignore  svn externals 
    4) ignore paths ignore by the git-svn bridge""")

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

def main():
    args = parse_cli_args()

    if not IsSvnWc():
        raise Exception("cwd is not an svn working copy: " + os.getcwd())

    if not IsGitSvnRepo():
        raise Exception("cwd is not a git-svn repo: " + os.getcwd())

    # find the git commit where HEAD branched of from the SVN branch
    (sha,gitSvnBranchPoint_SvnRev) = GetGitSvnBranchPointRev()

    # info logging
    baseRev = GetSvnWCBaseRev()
    if int(baseRev) < int(gitSvnBranchPoint_SvnRev):
        print("updating svn from " + baseRev + " to : " + gitSvnBranchPoint_SvnRev)
    elif int(baseRev) == int(gitSvnBranchPoint_SvnRev):
        print("svn WC is up to date at rev: " ,baseRev)
    else:
        assert int(baseRev) > int(gitSvnBranchPoint_SvnRev)
        print("downdating svn from " + baseRev + "to : " + gitSvnBranchPoint_SvnRev)

    # update svn to the relevant revision
    if args.dry_run:
        sys.exit(0)

    cmd = [ 'svn', 'up' 
            ,'--force'  # handle unversioned obstructions as changes
            , '--accept', 'working' # resolve conflict 
            , '--adds-as-modification' # prevent tree conflicts
            , '-r', gitSvnBranchPoint_SvnRev
    ]
    DebugLog.print(str(cmd))    
    subprocess.check_call(cmd)
                   

    sys.exit(0)
