from __future__ import print_function
import sys
import os
from git_svn.debug import *
import argparse
from git_svn.git import *
from git_svn.svn import *
import yaml
from collections import OrderedDict

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

    parser.add_argument("--svnExternalsConfigFile"
                    , help="config file describing all svn externals"
                    , default=".svnExternals.yml")
                   
    parser.add_argument("--source"
                    , help="explicitly specify the source of the external definitions"
                    , choices=["git-svn","svn"])

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

def svnExternalUrlDefinition(svnExternal):
    """ given an svn:external definition set on a specific folder in a working copy
    [-r <operativeRev>] <url>[@<pegRev>] <path>

    Then return only the first part without the path which identifies the external svn commit

    see also: http://svnbook.red-bean.com/en/1.7/svn.advanced.externals.html
    """
    __str = ""
    if svnExternal.operativeRev is not None:
        __str += "-r " + str(svnExternal.operativeRev) + " "

    __str += svnExternal.url

    if svnExternal.pegRev is not None:
        __str += '@' + str(svnExternal.pegRev)
    return __str

def svnExternalPath(svnExternal):
    """ given an svn:external definition set on a specific folder in a working copy
    [-r <operativeRev>] <url>[@<pegRev>] <path>

    Then return the path where to check the external out. I.e. this is the combination of
    the WC folder on which the external is defined and the <path> segment of the definition itself.

    see also: http://svnbook.red-bean.com/en/1.7/svn.advanced.externals.html
    """
    return os.path.join(svnExternal.svnWCFolderPath, svnExternal.path)


def main():
    args = parse_cli_args()

    if os.path.isfile(args.svnExternalsConfigFile):
        raise Exception("svnExternalsConfigFile already exists: " + args.svnExternalsConfigFile)

    if args.source is None: 
        if IsGitSvnRepo():    
            # if therws is a git-svn repo then lets assume it is the main Working copy
            # and git in favor of svn 
            svnExternals = GetSvnExternalsFromGitSvnBridge()
        elif IsSvnWc():
            # use svn WC info if available
            svnExternals = GetSvnExternalsFromLocalSvnWc()
        else:
            raise Exception("cwd is not a git-svn bridge nor an svn working copy")
    else:
        if args.source == "git-svn":  
            # if therws is a git-svn repo then lets assume it is the main Working copy
            # and git in favor of svn 
            svnExternals = GetSvnExternalsFromGitSvnBridge()
        elif args.source == "svn":  
            # use svn WC info if available
            svnExternals = GetSvnExternalsFromLocalSvnWc()
        else:
            raise Exception("cwd is not a git-svn bridge nor an svn working copy")


    print("#externals: " + str(len(svnExternals)))


    if len(svnExternals) == 0:
        # nothing to do :-)
        return 
        
    # build yaml config
    with open(args.svnExternalsConfigFile, 'wt') as f:
        svnRepoUrl =  svnExternals[0].hostRepoUrl
        f.write("svnRepoUrl: {}\n".format(svnRepoUrl))
        f.write("externals:\n")

        for svnExternal in svnExternals:
            assert svnRepoUrl == svnExternal.hostRepoUrl

            f.write("  - path: {}\n".format(svnExternalPath(svnExternal)))
            f.write("    externalDefinition: {}\n".format(svnExternalUrlDefinition(svnExternal)))
  

    sys.exit(0)

