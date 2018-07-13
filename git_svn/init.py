from __future__ import print_function

from six.moves import urllib

import sys
import os

from git_svn.debug import *
import argparse
import subprocess
from xml.etree import ElementTree as ET
from git_svn.svn import *



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

    parser.add_argument("--ignore-dir",
                        help="exclude an svn folder from git.",
                        default=[],
                        nargs="*")

    parser.add_argument("-r", "--revision",
                        help="specify the revision form where to start git svn fetch (defaults to svn BASE revision).")

    args = parser.parse_args()



    # register custom exception handler
    h = ExceptionHandle(args.debug)
    sys.excepthook = h.exception_handler

    DebugLog.enabled = args.debug
    with DebugLogScopedPush("cli arguments:"):
        DebugLog.print(str(args))
    
    return args


class IgnoreDirs:
    def __init__(self):
        self.ignoreDirs = []

    def hasIgnoreDirs(self):
        return len(self.ignoreDirs) > 0

    def appendDir(self, path):
        if not os.path.isdir(path):
            raise Exception("Path '%s' is not a folder" % path)

        path = path.replace('\\', '/')
        if path[-1] != '/':
            path += '/'
        self.ignoreDirs.append(path)

    
    def buildGitSvnIgnorePathRegex(self):
        return "(" + "|".join(self.ignoreDirs) + ")"

def main():
    global args
    args = parse_cli_args()

    if not IsSvnWc():
        raise Exception("cwd is not an svn working copy: " + os.getcwd())

    if IsSvnWcDirty():
        raise Exception("""svn working copy is dirty.
please commit or shelve your local changes so they can't be lost before initializing a git-svn bridge.""")

    ignoredDirs = IgnoreDirs()
    for p in args.ignore_dir:
        ignoredDirs.appendDir(p)

    xml = subprocess.check_output(["svn",  "info",  "--xml"]).decode()
    info_root = ET.fromstring(xml)

    n = info_root.findall("./entry/repository/root")
    assert 1 == len(n)
    root_url = n[0].text

    n = info_root.findall("./entry/relative-url")
    assert 1 == len(n)
    relative_url = urllib.parse.unquote(n[0].text)

    n = info_root.findall('./entry/commit')
    assert 1 == len(n)
    rev = int(n[0].get('revision'))

    if args.revision is not None:
        rev = int(args.revision)

    assert "^/" == relative_url[:2]
    branchpath = relative_url[2:]
    branchname = os.path.basename(relative_url)
    branchname = branchname.replace(' ',"_")

    if args.verbose:
        print("root-url: " + root_url)
        print("branch-path: " + branchpath)
        print("branchname: " + branchname)
        print("revision : " + str(rev))
        if ignoredDirs.hasIgnoreDirs():
            print("ignored-paths:\n" + "\n\t".join(ignoredDirs.ignoreDirs))

    if args.dry_run:
        return


    cli_cmd =["git", "svn",  "init", root_url]
    subprocess.check_output(cli_cmd)

    subprocess.check_output(["git", "config", "--local", "--unset-all", "svn-remote.svn.fetch"])
    cli_cmd = ['git',  "config", "--local",
        "--add", "svn-remote.svn.fetch",  "%s:refs/remotes/git-svn/%s" % (branchpath, branchname)]
    subprocess.check_output(cli_cmd)

    if ignoredDirs.hasIgnoreDirs():
        subprocess.check_output('git config --local --add svn-remote.svn.ignore-paths "%s"' % ignoredDirs.buildGitSvnIgnorePathRegex())


    # fetching in a svn checkout will fail
    # this failure is however harmless and can be ignored
    cli_cmd = ["git", "svn", "fetch", "-r", str(rev)]
    subprocess.call(cli_cmd)

    cli_cmd = ["git", "svn", "fetch"]
    subprocess.call(cli_cmd)

    sys.exit(0)
