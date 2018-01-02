from __future__ import print_function
import sys
import traceback
import os

from git_svn.debug import *
import argparse
import subprocess
from xml.etree import ElementTree as ET

args = []

def parse_cli_args():
    """parse the script input arguments"""
    parser = argparse.ArgumentParser(description="create a git svn bridge repo in an svn working copy")

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


class ExceptionHandle:
    """Exception handler for this cli"""

    def __init__(self, debug):
        self.debug = debug

    def exception_handler(self, exception_type, exception, tb):
        # format python exception
        print(str(exception_type.__name__) + " : " + str(exception))

        # print stack trace in debug mode only
        if (self.debug):
            traceback.print_tb(tb)

def main():
    with open(".git/info/exclude", 'wt') as f:
        # the .svn/ metadata folder
        f.write("## ignore all '.svn' folders\n")
        f.write("**/.svn/" + "\n")
        f.write("\n")

        # ignore svn externals
        f.write("## ignore all svn external checkouts\n")
        for (root, dirs, files) in os.walk("./"):
            if (".svn" in dirs):
                # root is an svn external as identified by the presence of a '.svn' folder
                # drop the relative qualifier
                assert root.startswith("./")
                path = root[2:]
                # git config required unix path separators (i.e. forward slash '/')
                path = path.replace("\\", "/")
                # append final path separator to ensure the rule only matches with folders
                path = path + "/"
                f.write(path + "\n")

            # prevent recursion into the following folders
            if (".git" in dirs):
                dirs.remove(".git")
            if (".svn" in dirs):
                dirs.remove(".svn")
        
        # migrate the svn:ignore property
        f.write("\n")        
        f.write("## mirror the \svn:ignore' property\n")
        svnIgnoreRules = subprocess.check_output("git svn show-ignore").decode()
        f.write(svnIgnoreRules + "\n")



                

    sys.exit(0)
