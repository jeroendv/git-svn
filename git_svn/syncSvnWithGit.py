from __future__ import print_function
import sys
import traceback
import os
import re

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
    parser = argparse.ArgumentParser(description=r"""update the svn working copy to the git branching point""")

    parser.add_argument("-v", "--verbose",
                    help="increase output verbosity",
                    action="store_true")

    parser.add_argument("-d", "--debug",
                    help="enable debug output",
                    action="store_true")

    parser.add_argument('--username',
                    help="svn user name")
    
    parser.add_argument('--password',
                    help="svn password")
                   

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
    global args
    args = parse_cli_args()

    if not IsGitWc():
        raise Exception("cwd is not a git repo: " + os.getcwd())

    if IsGitWcDirty():
        raise Exception("cwd is dirty git working copy, terminating due to risk of loosing changes: " + os.getcwd())
        


    if not IsSvnWc():
        clean_svn_checkout()
        sys.exit(0)

    if IsSvnWc():
        updated_existing_svnWC()
        sys.exit(0)
    


    
                   
def clean_svn_checkout():
    # find the git commit where HEAD branched of from the SVN branch
    # i.e. find the most recent contained commit with a log entry as follows
    # git-svn-id: http://vsrv-bele-svn1/svn/Software/Main/NMAPI/NMAPI_Main@72264 cfd94225-6148-4c34-bb2a-21ea3148c527
    cmd =  ['git', 'log', '--grep=^git-svn-id:', '--date-order', '-1']
    
    if args.username is not None:
        cmd += ['--username', args.username]

    if args.password is not None:
        cmd += ['--password', args.password]


    DebugLog.print(str(cmd))
    output = subprocess.check_output(cmd).decode()
    m = re.search(r"git-svn-id: ([^@]*)@([0-9]*)", output)
    url = m.group(1)
    svn_rev = int(m.group(2))

    
    cmd = ['svn', 'checkout',
        '--force',
        url + "@" + str(svn_rev),
        '.']
    DebugLog.print(str(cmd))
    if not args.dry_run:
        subprocess.check_call(cmd)
    
    sys.exit(0)
    

def updated_existing_svnWC():
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
