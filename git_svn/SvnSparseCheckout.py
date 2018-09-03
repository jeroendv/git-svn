from __future__ import print_function

import sys
import os
import yaml

from git_svn.debug import DebugLog,DebugLogScopedPush
from git_svn.debug import ExceptionHandle

import argparse
from  git_svn import svn
import subprocess

global args
args = []

def parse_cli_args():
    global args
    """parse the script input arguments"""
    parser = argparse.ArgumentParser(description="Svn Sparse checkout given a '.svnSparseCheckout'")

    parser.add_argument("-v", "--verbose",
                        help="increase output verbosity",
                        action="store_true")

    parser.add_argument("-d", "--debug",
                        help="enable debug output",
                        action="store_true")

    parser.add_argument("--username",
                        help="svn username")

    parser.add_argument("--password",
                        help="svn credentials")

    parser.add_argument("-N", "--dry-run",
                        help="Do not perform any actions, only simulate them.",
                        action="store_true")
                        
    parser.add_argument("-r", "--rev",
                        help="svn revision to checkout")

    parser.add_argument("configFilePath",
                        nargs="?",
                        default = ".svnSparseCheckout.yml",
                        help=".svnSparseCheckout file decscribing the sparse checkout")
    
    parser.add_argument("checkoutPath",
                        nargs="?",
                        default = ".",
                        help="path to perform the sparse checkout")

    args = parser.parse_args()



    # register custom exception handler
    h = ExceptionHandle(args.debug)
    sys.excepthook = h.exception_handler

    DebugLog.enabled = args.debug
    with DebugLogScopedPush("cli arguments:"):
        DebugLog.print(str(args))
    
    return args

def sparse_file_checkout(file):
    (head, tail) = os.path.split(file)

    # first checout the intermediate directories
    sparse_dir_checkout(head)

    # now checkout the file itself
    cmd = ['svn', 'update'
        ,'--force'
        , '--set-depth', 'immediates' 
        , '--accept=working'
        , os.path.join(args.checkoutPath, file)]   

    if args.rev is not None:
        cmd += ['-r' , args.rev]
        
    DebugLog.print(str(cmd))

    if not args.dry_run:
        subprocess.check_output(cmd)
    


def sparse_dir_checkout(dir):
    if len(dir) == 0:
        return

    assert dir[-1] != '/'
    assert dir[-1] != os.sep
    
    (head, tail) = os.path.split(dir)

    if svn.IsSvnWc(os.path.join(args.checkoutPath, dir)):
        # if dir is already versioned, then it got checked out earlier!
        # hence it must now be skipped, to prevent setting the depth back to empty!
        return

    # recursively checkout the parent directories first
    if len(head) > 0:
        sparse_dir_checkout(head)

    # checkout dir itself.
    cmd = ['svn', 'update'
        , '--force'
        , '--set-depth', 'empty'
        , os.path.join(args.checkoutPath, dir)]

    if args.rev is not None:
        cmd += ['-r' , args.rev]

    DebugLog.print(str(cmd))
    

    if not args.dry_run:
        subprocess.check_output(cmd)  


def main(arguments=None):
    # parse cli arguments if no arguments are given
    global args
    if arguments is None:
        parse_cli_args()
    else:
        args = arguments

    if svn.IsSvnWc(args.checkoutPath):
        raise Exception("checkoutPath arg is already an svn working copy, can not check out another in the same place: " + args.checkoutPath)

    if not os.path.isfile(args.configFilePath):
        raise Exception("the provided  config file does not exists: " + args.configFilePath)

    with open(args.configFilePath, 'rt') as f:
        sparseCheckout = yaml.load(f)
        DebugLog.print(str(sparseCheckout))

    cmd = ['svn', 'checkout'
        ,'--force'
        , '--depth', 'empty']

    if args.rev is not None:
        cmd += ['-r' , args.rev]

    if args.username is not None:
        cmd += ['--username', args.username]

    if args.password is not None:
        cmd += ['--password', args.password]
    
    cmd += [sparseCheckout['svnRepoUrl']
            , args.checkoutPath ] 

    DebugLog.print(str(cmd))

    if not args.dry_run:
        subprocess.check_output(cmd)

    for f in sparseCheckout['files']:
        sparse_file_checkout(f)



