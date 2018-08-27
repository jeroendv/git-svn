from __future__ import print_function
import sys
import os
from git_svn.debug import *
import argparse
from git_svn.git import *
from git_svn.svn import *
import yaml

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ProcessPoolExecutor

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

    parser.add_argument("--svnExternalsConfigFile"
                    , help="config file describing all svn externals"
                    , default=".svnExternals.yml")
                   

    parser.add_argument("-N", "--dry-run",
                        help="Do not perform any actions, only simulate them.",
                        action="store_true")

    parser.add_argument("-j", "--jobs"
                        , help="number of svn externals checkedout concurrently"
                        , type=int
                        , default=4)

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


def parseSvnExternalsConfigFile(file):
    with open(file,"rt") as f:
        svnExternalsConfig = yaml.load(f)

    example_yamlconfig = """svnRepoUrl: foobar
externals:
  - path: folder1
    externalDefinition: def1
  - path: folder2
    externalDefinition: def a
"""

    repoUrl = svnExternalsConfig['svnRepoUrl']

    svnExternals = []
    for e in svnExternalsConfig['externals']:
        path = e['path']
        externalDefinition  = e['externalDefinition']
        svnExternal = SvnExternal.parse(repoUrl, "./", externalDefinition + " " + path)

        svnExternals.append(svnExternal)

    
    return svnExternals


def main():
    global args
    args = parse_cli_args()
    
    if os.path.isfile(args.svnExternalsConfigFile):
        externalDefinitions = parseSvnExternalsConfigFile(args.svnExternalsConfigFile)
    elif IsGitSvnRepo():    
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
    with ThreadPoolExecutor(max_workers=args.jobs) as e:
        e.map(checkoutExternal, externalDefinitions)

    DebugLog.print("waiting for all externals to finish checking out.")
                       

    sys.exit(0)
