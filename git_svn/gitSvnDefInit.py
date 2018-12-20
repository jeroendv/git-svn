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
    "initialize a git-svn bridge in an existing git checkout from a .gitsvn.yml file")

    parser.add_argument("git_remote",
                    help="git remote tracking the git-svn branches",
                    nargs="?",
                    default="origin")

    parser.add_argument("-f", "--force",
                    help="force sync the git-svn tracking refs with git_remote",
                    action="store_true")

    parser.add_argument("-N", "--dry-run",
                        help="Do not perform any actions, only simulate them.",
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
    cli_cmd = ['git', 'svn', 'info']
    DebugLog.print(str(cli_cmd))
    if args.dry_run:
        return
    subprocess.call(cli_cmd)




def git_svn_init(url):
    """initialization of the git-svn bridge
    
    this function is idempotent. It will initialize the git-svn bridge irrespective of wheter 
    the bridge is already initialized or not 

    initialization will fail if the git repo has a git-svn bridge for another svn repo.
    """
    global args
    currentUrl = git_get_config_key("svn-remote.svn.url")
    
    if currentUrl is None:
        print("initializing the git-svn bridge for: " + url, flush=True)

        # not a git-svn bridge yet, so initialize it
        cli_cmd =["git", "svn",  "init", url]

        # remove the nonsensical auto generated svn.remote.svn.fetch config keys
        cli_cmd2 = ["git", "config", "--local", "--unset-all", "svn-remote.svn.fetch"]

        DebugLog.print(str(cli_cmd))
        DebugLog.print(str(cli_cmd2))

        if args.dry_run:
            return
        
        output1 = subprocess.check_output(cli_cmd).decode()
        output2 = subprocess.check_output(cli_cmd2).decode()
        return

    
    if currentUrl != url:
        raise Exception("this git repo already has a git-svn bridge setup for a different svn repo: " + currentUrl)
    
    # this git repo is already initialized correctly, nothing to do
    assert currentUrl == url
    DebugLog.print("git-svn bridge is already initalized for: " + url)

def add_git_svn_branch_configuration(svn_branch_path:str):
    """idenpotent git-svn branch configuration """
    global args

    branch_name = os.path.basename(svn_branch_path)

    git_ref = "refs/remotes/git-svn/{}".format(branch_name)

    svn_git_fetchMap = GitSvnConfigFetchDef()

    if svn_branch_path in svn_git_fetchMap and git_ref == svn_git_fetchMap[svn_branch_path]:
        # nothign to do this config key already exists
        DebugLog.print("svn-remote.svn.fetch config key already exists for: " + svn_branch_path)
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

    DebugLog.print(str(cli_cmd))
    if args.dry_run:
        return

    subprocess.check_output(cli_cmd)

def set_git_svn_branch_reference(svn_branch_path:str, git_remote:str):
    """idempotent git-svn branch reference creation"""
    global args
    branch_name = os.path.basename(svn_branch_path)

    svn_ref = "refs/remotes/git-svn/{}".format(branch_name)
    git_ref = "refs/remotes/{}/{}".format(git_remote, branch_name)

    svn_ref_branch_hash = branch_exists(svn_ref)
    git_ref_branch_hash = branch_exists(git_ref)

    # check if the git_ref exists
    if not git_ref_branch_hash:
        msg = """Failed to add git-svn tracking branch reference: {}
Source branch reference does not exists: {}
"""
        msg = msg.format(svn_ref, git_ref)
        raise Exception(msg)
    
    elif not svn_ref_branch_hash:
        assert(git_ref_branch_hash)
        # create the svn branch ref based on the git branch ref
        print("Adding git-svn branch reference for: " + svn_branch_path, flush=True)
        cli_cmd = ['git', 'update-ref', svn_ref, git_ref]

        DebugLog.print(str(cli_cmd))
        if args.dry_run:
            return
        output = subprocess.check_output(cli_cmd).decode()
        DebugLog.print(output)
        return


    elif svn_ref_branch_hash == git_ref_branch_hash:
        # nothing to do: both branches exist and are the same
        assert svn_ref_branch_hash
        assert git_ref_branch_hash
        return

    else:  
        # both branches exists but are different
        assert svn_ref_branch_hash
        assert git_ref_branch_hash
        assert svn_ref_branch_hash != git_ref_branch_hash
        
        if not args.force:
            # BAIL-OUT: possible loss of data
            msg="git-svn branch reference already exists for: {}\nUse --force if you know what you are doing (remember you may always tag the branch if unsure!)" 
            raise Exception(msg.format(svn_branch_path))
        else:
            assert args.force
            # assume the user know what he is doing
            # create the svn branch ref based on the git branch ref
            print("moving git-svn branch reference for: " + svn_branch_path, flush=True)
            cli_cmd = ['git', 'update-ref', svn_ref, git_ref]

            DebugLog.print(str(cli_cmd))
            if args.dry_run:
                return
            output = subprocess.check_output(cli_cmd).decode()
            DebugLog.print(output)
            return
    
    # BUG: all possible cases should have been handled.
    # one should not get here!
    assert False
    



def add_git_svn_ignore_paths(ignore_paths:list):
    """add the ignore_paths to the git-svn bridge config
    """
    global args

    # nothing to do if nothing is ignored
    if not ignore_paths:
        assert len(ignore_paths) == 0
        return

    # fail if the config key is already set
    cli = ["git", "config", "--local", "--get", "svn-remote.svn.ignore-paths"]
    rc = subprocess.call(cli)
    if rc == 0:
        raise Exception("the git-svn bridge already has a svn-remote.svn.ignore-paths config key")

    # set the config key
    configStr = "(" + "|".join(ignore_paths) + ")"
    assert configStr != "()"
    cli_cmd = ["git", "config", "--local", 
        "svn-remote.svn.ignore-paths", configStr]
    DebugLog.print(str(cli_cmd))
    if args.dry_run:
        return
    subprocess.check_output(cli_cmd)


def git_get_config_key(key:str) -> (None, str):
    """fetch a local git configuration key value
    return None if not set
    return value otherwise (could be the empty string)"""

    try:
        cli = ["git", "config", "--local", "--get", key]
        output = subprocess.check_output(cli).decode()
        output = output.splitlines()
        assert len(output) == 1
        return output[0]

    except subprocess.CalledProcessError as e:
        assert e.returncode == 1 # a return code other then 1 means there is a bug!
        return None


def branch_exists(git_ref:str) -> str:
    """check if a certain branch exists
    returns "" if it does not exists (which evaluates to False)
    return the hash value if it does exists (which evaluates to True)"""
    # this can be executed even in dry_run mode since it doesn't make any changes
    try:
        hash_value = subprocess.check_output(['git', 'show-ref', '--hash', '--verify', git_ref]).decode()
        return hash_value
    except subprocess.CalledProcessError as e:
        return "" 

    

def GitSvnConfigFetchDef():
    try:
        # this can be executed even in dry_run mode since it doesn't make any changes
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

    




    
    

    


    