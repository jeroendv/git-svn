"""
initialize a git-svn bridge in an existing git working copy
based on a git-svn bridge definition described in a .gitsvn.yml file
"""

import argparse
import sys
import os
import subprocess
from git_svn.debug import *
from git_svn import git
import yaml

# global script cli arguments
args = []

def parse_cli_arg():
    """parse the script input arguments"""
    parser = argparse.ArgumentParser(description=
    "initialize a git-svn bridge in an existing git checkout from a .git-svn.yml file")

    parser.add_argument("git_remote",
                    help="git remote tracking the git-svn branches",
                    nargs="?",
                    default="origin")

    parser.add_argument("-f", "--force",
                    help="force sync the git-svn tracking refs with git_remote",
                    action="store_true")

    parser.add_argument("-d", "--debug",
                    help="enable debug output",
                    action="store_true")


    args = parser.parse_args()

    # register custom exception handler
    h = ExceptionHandle(args.debug)
    sys.excepthook = h.exception_handler

    # initialize the DebugLog singleton
    DebugLog.enabled = args.debug
    
    # log the cli arguments
    with DebugLogScopedPush("cli arguments:"):
        DebugLog.print(str(args))
    
    return args


def main():
    global args
    args = parse_cli_arg()

    # sanity checking
    if not git.IsGitWc():
        raise Exception("cwd is not a git directory: " + os.getcwd())

    if git.IsGitWcDirty():
        raise Exception("git wc is dirty. please commit or stash local changes first.")

    if not os.path.isfile(".gitsvn.yml"):
        raise Exception("missing git-svn bridge definition, no '.gitsvn.yml' file found.")

    with open(".gitsvn.yml", "tr") as f:
        git_svn_def = GitSvnDef.parseConfig(f.read())

   
    git_svn_init(git_svn_def.url)

    # add config key and git branch ref for each branch
    for branchpath in git_svn_def.branches:
        add_git_svn_branch_configuration(branchpath)
        set_git_svn_branch_reference(branchpath, args.git_remote)

    # add the ignore-paths config key
    add_git_svn_ignore_paths(git_svn_def.ignore_paths)

    # trick git-svn into rebuilding the rev_map by querying the svn info
    subprocess.call(['git', 'svn', 'info'])




def git_svn_init(url):
    """initialization of the git-svn bridge
    
    this function is idempotent. It will initialize the git-svn bridge irrespective of wheter 
    the bridge is already initialized or not 

    initialization will fail if the git repo has a git-svn bridge for another svn repo.
    """
    currentUrl = GitSvnUrl()
    
    if currentUrl is None:
        print("initializing the git-svn bridge for: " + url, flush=True)

        # not a git-svn bridge yet, so initialize it
        cli_cmd =["git", "svn",  "init", url]
        output = subprocess.check_output(cli_cmd).decode()
        
        # remove the nonsensical auto generated svn.remote.svn.fetch config keys
        subprocess.check_output(["git", "config", "--local", "--unset-all", "svn-remote.svn.fetch"])
        return 
    
    if currentUrl != url:
        raise Exception("this git repo already has a git-svn bridge setup for a different svn repo: " + currentUrl)
    
    # this git repo is already initialized correctly, nothing to do
    assert currentUrl == url
    print("git-svn bridge is already initalized for: " + url, flush=True)

def add_git_svn_branch_configuration(svn_branch_path:str):
    """idenpotent git-svn branch configuration """
    branch_name = os.path.basename(svn_branch_path)

    git_ref = "refs/remotes/git-svn/{}".format(branch_name)

    svn_git_fetchMap = GitSvnConfigFetchDef()

    if svn_branch_path in svn_git_fetchMap and git_ref == svn_git_fetchMap[svn_branch_path]:
        # nothign to do this config key already exists
        print("svn-remote.svn.fetch config key already exists for: " + svn_branch_path, flush=True)
        return 
    
    if branch_name in svn_git_fetchMap:
        assert git_ref != svn_git_fetchMap[svn_branch_path]
        raise Exception("""git branch is already tracked by: {}
Can't add second tracking branch reference: {}""".format(svn_git_fetchMap[svn_branch_path], git_ref))
    
    if git_ref in svn_git_fetchMap.values():
        existing_svn_path = None
        for (k,v) in svn_git_fetchMap.items():
            if v == git_ref:
                existing_svn_path = k
                break
        raise Exception("""git branch refernce is already tracking: {existing_svn_path}
the same branch reference can't track a second svn path: {}""".format("", svn_branch_path))


    # add the svn-remote.svn.fetch config key as it does not yet exists
    print("adding svn-remote.svn.fetch config key to track: " + svn_branch_path, flush=True)
    cli_cmd = ['git',  "config", "--local",
        "--add", "svn-remote.svn.fetch",  "%s:refs/remotes/git-svn/%s" % (svn_branch_path, branch_name)]
    subprocess.check_output(cli_cmd)

def set_git_svn_branch_reference(svn_branch_path:str, git_remote:str):
    """idempotent git-svn branch reference creation"""
    branch_name = os.path.basename(svn_branch_path)

    svn_ref = "refs/remotes/git-svn/{}".format(branch_name)
    git_ref = "refs/remotes/{}/{}".format(git_remote, branch_name)

    # check if the git_ref exists
    if not branch_exists(git_ref):
        msg = """Failed to add git-svn tracking branch reference: {}
Source branch reference does not exists: {}
"""
        msg = msg.format(svn_ref, git_ref)
        raise Exception(msg)

    if branch_exists(svn_ref) and not args.force:
        # the branch reference alreasy exists, nothing to do :-)
        print("git-svn branch reference already exists for: " + svn_branch_path, flush=True)

        return 


    assert (not branch_exists(svn_ref) or           # no git-svn tracking branch exists, yet
        ( branch_exists(svn_ref) and args.force))   # or the git-svn tracking branch is forcibly updated

    # create the svn branch ref based on the git branch ref
    print("Adding git-svn branch reference for: " + svn_branch_path, flush=True)
    cli_cmd = ['git', 'update-ref', svn_ref, git_ref]
    output = subprocess.check_output(cli_cmd).decode()
    DebugLog.print(output)

def add_git_svn_ignore_paths(ignore_paths:list):
    """add the ignore_paths to the git-svn bridge config
    """

    # fail if the config key is already set
    cli = ["git", "config", "--local", "--get", "svn-remote.svn.ignore-paths"]
    rc = subprocess.call(cli)
    if rc == 0:
        raise Exception("the git-svn bridge already has a svn-remote.svn.ignore-paths config key")

    # set the config key
    configStr = "(" + "|".join(ignore_paths) + ")"
    cli = ["git", "config", "--local", 
        "svn-remote.svn.ignore-paths", configStr]
    subprocess.check_output(cli)


def branch_exists(git_ref:str) -> bool:
    """check if a certain branch exists"""
    rc = subprocess.call(['git', 'show-ref', '--quiet', '--verify', git_ref])
    return rc == 0



def GitSvnUrl() -> str :
    try: 
        output = subprocess.check_output(['git','config', '--local', '--get', 'svn-remote.svn.url']).decode()

        # these should be only 1 output line containing the url of the svn server
        output = output.splitlines()
        assert len(output) == 1

        return output[0]
    except subprocess.CalledProcessError as e:
        assert e.returncode == 1 # a return code other then 1 means there is a bug!
        return None

def GitSvnConfigFetchDef():
    try:
        output = subprocess.check_output(['git', 'config', '--local', '--get-all', 'svn-remote.svn.fetch']).decode()

        git_svn_map = {}
        for line in output.splitlines():
            [svn_path, git_ref] = line.split(':')
            git_svn_map[svn_path] = git_ref

        return git_svn_map

    except subprocess.CalledProcessError as e:
        assert e.returncode == 1 # a return code other then 1 means there is a bug!
        return dict()

class GitSvnDef(object):
    @property
    def url(self):
        """the url of the svn repository
        
        SA git config key: svn-remote.svn.url
        """
        return self._url
    @property
    def branches(self):
        """the set of branches to be tracked

        a branch is identified by its path in the repository
        SA git config key svn-remote.svn.fetch
        """
        return self._branches

    @property
    def ignore_paths(self):
        """the set of repository paths that are to be ignored
        
        each entry is a regex and any path that matches it will be ignored 
        by the git-svn bridge.

        SA git config key: svn-remote.svn.ignore-paths
        """
        return self._ignore_paths

    def __init__(self, url, branches, ignore_paths):
        self._url = url
        self._branches = set(branches)
        self._ignore_paths = set(ignore_paths)

    @classmethod
    def parseConfig(cls, config:str):
        """parse a yaml configuration string) into a `GitSvnDef`"""
        # delegate reading and parsing config to yaml module
        yamlConfig = yaml.load(config)

        # check config data
        # 1) url
        if 'url' not in yamlConfig:
            raise Exception("missing key 'url'")
        if type(yamlConfig['url']) is not str:
            raise Exception("expected a url value for the url key. but got" + str(yamlConfig['url']))
        # 2) branches
        if 'branches' not in yamlConfig:
            raise Exception("missing key 'branches'. At least one svn branch expected")
        if type(yamlConfig['branches']) is not list:
            raise Exception("expected a list for the branches key. but got" + str(yamlConfig['branches']))
        for b in yamlConfig['branches']:
            if type(b) is not str:
                raise Exception("Each of the branches key list items should be a url string.  but got" + str(yamlConfig['url']))

        # 3) ignore-paths
        if 'ignore-paths' not in yamlConfig:
            return GitSvnDef(yamlConfig['url'], yamlConfig['branches'], [])

        if type(yamlConfig['ignore-paths']) is not list:
            raise Exception("expected a list of ignore-paths, but got " + str(yamlConfig['ignore-paths']))
        
        for p in yamlConfig['ignore-paths']:
            if type(p) is not str:\
                raise Exception("Each of the ignore-paths key list items should be a str, but got " + str(p))
        

        return GitSvnDef(yamlConfig['url'], yamlConfig['branches'], yamlConfig['ignore-paths'])

    




    
    

    


    