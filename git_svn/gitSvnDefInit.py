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
    "initialize a git-svn bridge in an existing git working copy")

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
    for branch in git_svn_def.branches:
        add_git_svn_branch_configuration(branch)
        add_git_svn_branch_reference(branch)

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

def add_git_svn_branch_configuration(branch: GitSvnBranchDef):
    """idenpotent git-svn branch configuration """
    branch_set = GitSvnConfigBranchSet()

    if branch in branch_set:
        # nothign to do this config key already exists
        print("svn-remote.svn.fetch config key already exists for: " + svn_branch_path, flush=True)
        return 
    
    b = branch_set.get_branch_for_svn_path(branch.svn_path)
    if b is not None:
        assert branch.git_svn_ref != b.git_svn_ref
        raise Exception("""svn path: {}
is already tracked by: {}
Can't add second tracking branch reference: {}""".format(branch.svn_path, b.git_svn_ref, branch.git_svn_ref))
    
    b = branch_set.get_branch_for_git_svn_ref(branch.git_svn_ref)
    if b is not None:
        assert branch.svn_path != b.svn_path
        raise Exception("""git branch: {}
is already tracking svn path : {}
the same branch reference can't track a second svn path: {}""".format(b.git_svn_ref, b.svn_path, branch.svn_path))


    # add the svn-remote.svn.fetch config key as it does not yet exists
    print("adding svn-remote.svn.fetch config key to track: " + branch.svn_path, flush=True)
    cli_cmd = ['git',  "config", "--local",
        "--add", "svn-remote.svn.fetch",  branch.unparse()]
    subprocess.check_output(cli_cmd)

def add_git_svn_branch_reference(branch: GitSvnBranchDef, remote = "origin"):
    """idempotent git-svn branch reference creation"""
    branch_name = os.path.basename(svn_branch_path)

    if branch_exists(branch.git_svn_ref):
        # the branch reference alreasy exists, nothing to do :-)
        print("git-svn branch reference already exists for: " + svn_branch_path, flush=True)

        return 

    # check if the git_ref exists
    if not branch_exists(branch.git_remote_ref):
        msg = """Failed to add git-svn tracking branch reference: {}
Source branch reference does not exists: {}
"""
        msg = msg.format(branch.git_svn_ref, branch.git_remote_ref)
        raise Exception(msg)

    # create the svn branch ref based on the git branch ref
    print("Adding git-svn branch reference for: " + svn_branch_path, flush=True)
    cli_cmd = ['git', 'update-ref', branch.git_svn_ref, branch.git_remote_ref]
    output = subprocess.check_output(cli_cmd).decode()
    DebugLog.print(output)


def branch_exists(git_ref):
    """check if a certain branch exists"""
    rc = subprocess.call(['git', 'show-ref', '--quiet', '--verify', git_ref])
    return rc == 0



def GitSvnUrl():
    try: 
        output = subprocess.check_output(['git','config', '--local', '--get', 'svn-remote.svn.url']).decode()

        # these should be only 1 output line containing the url of the svn server
        output = output.splitlines()
        assert len(output) == 1

        return output[0]
    except subprocess.CalledProcessError as e:
        assert e.returncode == 1 # a return code other then 1 means there is a bug!
        return None

def GitSvnConfigBranchSet():
    try:
        output = subprocess.check_output(['git', 'config', '--local', '--get-all', 'svn-remote.svn.fetch']).decode()

        branch_set = BranchSet()
        for line in output.splitlines():
            branch_set.append(Branch(line))

        return branch_set

    except subprocess.CalledProcessError as e:
        assert e.returncode == 1 # a return code other then 1 means there is a bug!
        return BranchSet()
        


class GitSvnDef(object):
    @property
    def url(self):
        return self._url
    @property
    def branches(self):
        return self._branch_set

    def __init__(self, url):
        self._url = url
        self._branch_set = BranchSet()


    @classmethod
    def parseConfig(cls, config:str):
        """parse a yaml configuration string) into a `GitSvnDef`"""
        # delegate reading and parsing config to yaml module
        yamlConfig = yaml.load(config)

        # check config data
        if 'url' not in yamlConfig:
            raise Exception("missing key 'url'")
        if type(yamlConfig['url']) is not str:
            raise Exception("expected a url value for the url key. but got" + str(yamlConfig['url']))
        if 'branches' not in yamlConfig:
            raise Exception("missing key 'branches'. At least one svn branch expected")
        
        if type(yamlConfig['branches']) is not list:
            raise Exception("expected a list for the branches key. but got" + str(yamlConfig['branches']))
        for b in yamlConfig['branches']:
            if type(b) is not str:
                raise Exception("Each of the branches key list items should be a url string.  but got" + str(yamlConfig['url']))

        # 
        git_svn_def = GitSvnDef(yamlConfig['url'])
        for b in yamlConfig['branches']:
            git_svn_def.branches.append(GitSvnBranchDef(b))

        return git_svn_def



class Branch(Object):
    """git config svn-remote.svn.fetch value"""
    
    @property
    def svn_path(self):
        """svn repo path to the branch"""
        return self._svn_path
    
    @property
    def branch_name(self):
        """name of the branch (same for git and svn)"""
        return os.path.basename(self._svn_path)
    
    @property
    def git_svn_ref(self):
        """the git-svn remote tracking branch reference
        
        This is the git remote tracking branch that tracks the svn branch, 
        I.e. it is the branch managed by the git-svn bridge """
        return self._git_svn_ref

    def __init__(self, svn_path, git_svn_ref):
        self._svn_path = svn_path
        self._git_svn_ref

    @classmethod
    def parse(cls, git_config_str):
        [svn_path, git_svn_ref] = git_config_str.split(':')
        return Branch(svn_path, git_svn_ref)

    def unparse(self):
        return self.svn_path + ":" + self.git_svn_ref

class BranchSet(Object):
    """a git-svn bridge can track multiple svn branches at once"""

    @property
    def __iter__(self):
        return self._branches

    def __init__self(self):
        self._branches = []

    def get_branch_for_svn_path(self, svn_path):
        for b in self._branches:
            if b.svn_path == svn_path:
                return b
        
        return None

    def get_branch_for_git_svn_ref(self, git_svn_ref):
        for b in self._branches:
            if b.git_svn_ref == git_svn_ref:
                return b

        return None
    
    def append(self, branch:Branch):
        if self.get_branch_for_svn_path(branch.svn_path) is not None:
            raise Exception("svn_path '{}' is already being tracked".format(branch.svn_path))
        
        if self.get_branch_for_git_svn_ref(branch.git_svn_ref) is not None:
            raise Exception("git_svn_ref '{}' is already being tracking an svn path".format(branch.git_svn_ref))
        
        self._branches.append(branch)

    def __in__ (self, branch:Branch):
        b = self.get_branch_for_svn_path(branch.svn_path)
        if b is None:
            return False
        else:
            return b.git_svn_ref == branch.git_svn_ref


class GitSvnBranchDef(Branch):
    def git_remote_ref(self, remote=origin):
        """the reference of this branch as tracked by another git repo.

        I.e. it is git_svn_ref branch duplicated on a global git repo"""

        return "refs/remotes/{}/{}".format(remote, self.branch_name)

    def __init__(self, svn_path):
        super(svn_path, self.__git_svn_ref(svn_path))

    def __git_svn_ref(self, svn_path):
        branch_name = os.path.basename(svn_path)
        return "refs/remotes/git-svn/{}".format(branch_name)
    


