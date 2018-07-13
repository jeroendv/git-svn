from __future__ import print_function
import sys
import os
from git_svn.debug import *
import argparse
import subprocess
from xml.etree import ElementTree as ET
from git_svn.git import *
from git_svn.svn import *

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
    
    DebugLog.print("cwd : "+os.getcwd())
    
    return args

def DeriveHistoricSvnExternals(historicRev, svnExternal):
    """Derive historic SvnExternal.

    a historic svn external has the operative and peg revision set to the
    external HEAD revision at the time of `historicRev`. """
    # obtain dateRev specifier of the historic Revision
    assert type(svnExternal) is  SvnExternal
    text = subprocess.check_output(['svn', 'info', '--xml','-r', str(historicRev), svnExternal.hostRepoUrl])
    infoXml = ET.fromstring(text)
    dateRevStr = infoXml.find('entry/commit/date').text
    dateRevStr = '{' + dateRevStr + '}'
    
    # obtain the external head revision at the given time
    text = subprocess.check_output(['svn', 'info', '--xml','-r', dateRevStr , svnExternal.QualifiedUrl])
    infoXml = ET.fromstring(text)
    revStr = infoXml.find('entry/commit').get('revision')

    # return copy of svn External with overrules operative and peg revision
    return SvnExternal(svnExternal.hostRepoUrl,
                    svnExternal.svnWCFolderPath,
                    revStr,
                    svnExternal.url,
                    revStr,
                    svnExternal.path)    



def main():
    args = parse_cli_args()

    if IsGitSvnRepo():    
        # if there is a git-svn repo then lets assume it is the main Working copy
        # and use git in favor of svn 
        (sha, historicRev) = GetGitSvnBranchPointRev()
        externalDefinitions = GetSvnExternalsFromGitSvnBridge()   
    elif IsSvnWc():
        # use svn WC info if available
        historicRev = GetSvnWCBaseRev()
        externalDefinitions = GetSvnExternalsFromLocalSvnWc() 
    else:
        raise Exception("not a git-svn bridge nor an svn working copy: " + os.getcwd())

    print("#externals: " + str(len(externalDefinitions)))

    # generate the list of historic externals
    historicExternals = []
    for d  in externalDefinitions:
        print(d.svnWCFolderPath + " : " + str(d))
        historicExternal = DeriveHistoricSvnExternals(historicRev, d)
        print("  -> " + str(historicExternal))
        historicExternals.append(historicExternal)

    # stop if dry run
    if args.dry_run:
        sys.exit(0)

    # checkout/update the historic externals in the SVN WC
    for externalDef in historicExternals:
        print(externalDef.svnWCFolderPath + " " + str(externalDef))
        checkoutSvnExternal(externalDef)               

    sys.exit(0)
