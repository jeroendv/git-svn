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

    if os.path.isfile(args.svnExternalsConfigFile):
        raise Exception("svnExternalsConfigFile already exists: " + args.svnExternalsConfigFile)

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


    if len(externalDefinitions) == 0:
        # nothing to do :-)
        return 
        
    # build yaml config
    with open(args.svnExternalsConfigFile, 'wt') as f:
        svnRepoUrl =  externalDefinitions[0].hostRepoUrl
        f.write("svnRepoUrl: {}\n".format(svnRepoUrl))
        f.write("externals:\n")

        for externalDef in externalDefinitions:
            assert svnRepoUrl == externalDef.hostRepoUrl

            f.write("  - path: {}\n".format(externalDef.svnWCFolderPath))
            f.write("    externalDefinition: {}\n".format(str(externalDef)))
  

    sys.exit(0)

