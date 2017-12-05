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
    global args
    args = parse_cli_args()
    xml = subprocess.check_output("svn info --xml").decode()
    info_root = ET.fromstring(xml)

    n = info_root.findall("./entry/repository/root")
    assert 1 == len(n)
    root_url = n[0].text

    n = info_root.findall("./entry/relative-url")
    assert 1 == len(n)
    relative_url = n[0].text

    n = info_root.findall('./entry/commit')
    assert 1 == len(n)
    rev = int(n[0].get('revision'))

    assert "^/" == relative_url[:2]
    branchpath = relative_url[2:]
    branchname = os.path.basename(relative_url)

    cli_cmd = 'git svn init "%s"' % root_url
    subprocess.check_output(cli_cmd)

    subprocess.check_output("git config --local --unset-all svn-remote.svn.fetch")
    cli_cmd = 'git config --local --add svn-remote.svn.fetch    "%s:refs/remotes/git-svn/%s"' % (branchpath, branchname)
    subprocess.check_output(cli_cmd)

    # fetching in a svn checkout will fail
    # this failure is however harmless and can be ignored
    cli_cmd = "git svn fetch -r %i" % rev
    subprocess.call(cli_cmd)
    subprocess.check_output("git checkout --force master")

    sys.exit(0)
