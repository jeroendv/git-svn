from __future__ import print_function
import sys
import os
from git_svn.debug import *
import argparse
import subprocess
from xml.etree import ElementTree as ET
from git_svn.git import *
from git_svn.svn import *

if sys.version_info < (3,5):
    print("Script is being run with a too old version of Python. Needs 3.5.")
    sys.exit(0)


args = []

def parse_cli_args():
    """parse the script input arguments"""
    parser = argparse.ArgumentParser(description=r"""graphical view of svnWC to git-svn WC state""")

    parser.add_argument("-d", "--debug",
                    help="enable debug output",
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



    # sanity checks

    if not IsGitSvnRepo():
        raise Exception("cwd is not a git-svn working copy: " + os.getcwd())

    if not IsSvnWc():
        raise Exception("cwd is not an svn working copy: " + os.getcwd())

    svnBaseRev = int(GetSvnWCBaseRev())
    svnDirtyFlag = " (*)" if IsSvnWcDirty() else ""

    (gitSvnBranchPoint_gitSHA, svnGitBranchPoint_svnRev) = GetGitSvnBranchPointRev()
    svnGitBranchPoint_svnRev = int(svnGitBranchPoint_svnRev)

    gitDirtyFlag = " (*)" if IsGitWcDirty() else ""

    gitBranchAheadCount = GitCountCommits(gitSvnBranchPoint_gitSHA, GetCurrentGitBranch())

    if svnBaseRev == svnGitBranchPoint_svnRev and gitBranchAheadCount == 0:
        print("* rev {} (svn{}, git{})".format(svnBaseRev, svnDirtyFlag, gitDirtyFlag))
    elif svnBaseRev == svnGitBranchPoint_svnRev and gitBranchAheadCount > 0:
        print("  * git +{}{}".format(gitBranchAheadCount, gitDirtyFlag))
        print(" /")
        print("* rev {} (svn{})".format(svnBaseRev, svnDirtyFlag, gitDirtyFlag))
    elif svnBaseRev < svnGitBranchPoint_svnRev and gitBranchAheadCount == 0:
        aheadCount = SvnCountCommits(svnBaseRev, svnGitBranchPoint_svnRev)
        print("* rev {} (git +{}{})".format(svnGitBranchPoint_svnRev, aheadCount, gitDirtyFlag))
        print("|")
        print("* rev {} (svn{})".format(svnBaseRev, svnDirtyFlag))
    elif svnBaseRev < svnGitBranchPoint_svnRev and gitBranchAheadCount > 0:
        aheadCount = SvnCountCommits(svnBaseRev, svnGitBranchPoint_svnRev)
        print(" * (git +{}{})".format(gitBranchAheadCount, gitDirtyFlag))
        print(" /")
        print("* rev {} (+{})".format(svnGitBranchPoint_svnRev, aheadCount))
        print("|")
        print("* rev {} (svn{})".format(svnBaseRev, svnDirtyFlag))
    elif  svnGitBranchPoint_svnRev < svnBaseRev and gitBranchAheadCount == 0:
        aheadCount = SvnCountCommits(svnGitBranchPoint_svnRev, svnBaseRev)
        print("* rev {} (svn +{}{})".format(svnBaseRev, aheadCount, svnDirtyFlag))
        print("|")
        print("* rev {} (git{})".format(svnGitBranchPoint_svnRev, gitDirtyFlag))
    elif  svnGitBranchPoint_svnRev < svnBaseRev and gitBranchAheadCount > 0:
        aheadCount = SvnCountCommits(svnGitBranchPoint_svnRev, svnBaseRev)
        print("* rev {} (svn +{}{})".format(svnBaseRev, aheadCount, svnDirtyFlag))
        print("| * (git +{}{})".format(gitBranchAheadCount, gitDirtyFlag))
        print("|/")
        print("* rev {} ".format(svnGitBranchPoint_svnRev))
    else:
        raise Exception("Impossible state!")


    sys.exit(0)
