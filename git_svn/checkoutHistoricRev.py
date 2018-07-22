from __future__ import print_function
import sys
import os
from git_svn.debug import DebugLog,DebugLogScopedPush
from git_svn.debug import ExceptionHandle
import argparse
import subprocess
from xml.etree import ElementTree as ET
from git_svn import svn,git

if sys.version_info < (3,5):
    print("Script is being run with a too old version of Python. Needs 3.5.")
    sys.exit(0)

args = []

def parse_cli_args():
    """parse the script input arguments"""
    parser = argparse.ArgumentParser(description=r"""historic svn checkout given a time instead of a revision
http://svnbook.red-bean.com/en/1.7/svn.tour.revs.specifiers.html""")

    parser.add_argument("-v", "--verbose",
                    help="increase output verbosity",
                    action="store_true")

    parser.add_argument("-d", "--debug",
                    help="enable debug output",
                    action="store_true")
                   

    parser.add_argument("-N", "--dry-run",
                        help="Do not perform any actions, only simulate them.",
                        action="store_true")
    parser.add_argument('-r', "--revision",
                        help="revision date e.g. {2006-02-17 15:30}")

    args = parser.parse_args()



    # register custom exception handler
    h = ExceptionHandle(args.debug)
    sys.excepthook = h.exception_handler

    DebugLog.enabled = args.debug
    with DebugLogScopedPush("cli arguments:"):
        DebugLog.print(str(args))
    
    DebugLog.print("cwd : "+os.getcwd())
    
    return args

def DeriveHistoricSvnExternals(historicDateRevStr, svnExternal):
    """Derive historic SvnExternal."""
    
    # obtain the external head revision at the given time
    text = subprocess.check_output(['svn', 'info', '--xml','-r', historicDateRevStr , svnExternal.QualifiedUrl])
    infoXml = ET.fromstring(text)
    revStr = infoXml.find('entry/commit').get('revision')

    # return copy of svn External with overrules operative and peg revision
    return svn.SvnExternal(svnExternal.hostRepoUrl,
                    svnExternal.svnWCFolderPath,
                    revStr,
                    svnExternal.url,
                    revStr,
                    svnExternal.path)    



def main():
    args = parse_cli_args()



    # sanity checks
    if args.revision is None:
        raise Exception("Missing '-r {date revision}' flag")

    if not args.revision.startswith('{') or not args.revision.endswith('}'):
        raise Exception("invalid date revision : " + args.revision)

    if git.IsGitWc() and git.IsGitWcDirty():
        raise Exception("""git working copy is dirty.
please first commit or stash your local changes so they can't be lost.""")

    if not svn.IsSvnWc():
        raise Exception("cwd is not an svn working copy: " + os.getcwd())

    if svn.IsSvnWcDirty():
        raise Exception("""svn working copy is dirty.
please first commit or shelve your local changes so they can't be lost.""")

    # obtain historic commit rev 
    text = subprocess.check_output(['svn', 'info', '--xml','-r', args.revision])
    infoXml = ET.fromstring(text)
    rev = infoXml.find('entry').get('revision')

    print("update to rev: "+ rev)

    # stop if dry run
    if args.dry_run:
        sys.exit(0)

    # update WC
    if git.IsGitSvnRepo():
        commit_sha = git.GetAssociatedGitShaForSvnRev(int(rev))
        git.checkout(commit_sha)   
    else:
        svn.checkout(int(rev))

    # do historic checkout for each of the externals
    # obtains externals for current WC
    externalDefinitions = []
    if git.IsGitSvnRepo():
        externalDefinitions = git.GetSvnExternalsFromGitSvnBridge()
    else:
        externalDefinitions = svn.GetSvnExternalsFromLocalSvnWc()
    print("#externals: " + str(len(externalDefinitions)))

    # generate the list of historic externals
    historicExternals = []
    for d  in externalDefinitions:
        print(d.svnWCFolderPath + " : " + str(d))
        historicExternal = DeriveHistoricSvnExternals(args.revision, d)
        print("  -> " + str(historicExternal))
        historicExternals.append(historicExternal)

    # checkout/update the historic externals in the SVN WC
    for externalDef in historicExternals:
        print(externalDef.svnWCFolderPath + " " + str(externalDef))
        svn.checkoutSvnExternal(externalDef)               

    sys.exit(0)
