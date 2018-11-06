import subprocess
from git_svn.debug import DebugLog
from git_svn import timeit
from git_svn import svn
import os
import re

@timeit
def IsGitWc():
    try: 
        subprocess.check_output(['git', 'status'])
        return True
    except subprocess.CalledProcessError:
        return False

@timeit
def IsGitWcDirty():
    text = subprocess.check_output(['git', 'status', "--short", '--untracked-files=no'])
    if len(text.splitlines()) == 0:
        return False
    else:
        return True

@timeit
def IsGitSvnRepo():
    try: 
        subprocess.check_output(['git','config', '--local', '--get-regexp', 'svn-remote.svn.url'])
        return True

    except subprocess.CalledProcessError as e:
        assert e.returncode == 1 # a return code other then 1 means there is a bug!
        return False


def GetCurrentGitBranch():
    output = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', '@']).decode()
    output = output.splitlines()
    assert len(output) == 1
    branchName = output[0]
    return branchName

@timeit
def GitCountCommits(start, end):
    output = subprocess.check_output(['git', 'log' ,'--oneline', start + ".." + end]).decode()
    return len(output.splitlines())


def GetAssociatedGitShaForSvnRev(rev_int):
    output = subprocess.check_output(['git', 'svn', 'find-rev', 'r'+str(rev_int)]).decode()
    output = output.splitlines()
    assert len(output) == 1
    commitSha = output[0]
    return commitSha

def checkout(commit_sha):
    subprocess.check_output(['git', 'checkout', commit_sha])

    

@timeit
def GetGitSvnBranchPointRev():
    # find the git commit where HEAD branched of from the SVN branch
    cmd =  ['git', 'log', '--grep=^git-svn-id:', '--date-order', '-1', "--format=%H"]
    DebugLog.print(str(cmd))
    output = subprocess.check_output(cmd).decode()
    DebugLog.print(output)
    output = output.splitlines()
    assert len(output) == 1
    gitSvnBranchPoint_gitSHA = output[0]
    
    # determine the Svn commit revision associated with the branch point
    cmd  = ['git', 'svn' , 'find-rev', '-B', str(gitSvnBranchPoint_gitSHA)]
    DebugLog.print(str(cmd))
    output = subprocess.check_output(cmd).decode()
    DebugLog.print(output)    
    output = output.splitlines()
    assert len(output) == 1
    gitSvnBranchPoint_SvnRev = output[0]
    DebugLog.print("git-svn branchpoint (git-Sha - svn-Rev): " + gitSvnBranchPoint_gitSHA + " - " + gitSvnBranchPoint_SvnRev)
    return (gitSvnBranchPoint_gitSHA, gitSvnBranchPoint_SvnRev)

def find_svn_branch_point_for_current_gitbranch():
    """ find the svn branch point for the current git branch

    return a (qualified_url:str, svn_rev:str) tuple
    """
    # find the git commit where HEAD branched of from the SVN branch
    # i.e. find the most recent contained commit with a log entry as follows
    # git-svn-id: http://vsrv-bele-svn1/svn/Software/Main/NMAPI/NMAPI_Main@72264 cfd94225-6148-4c34-bb2a-21ea3148c527
    cmd =  ['git', 'log', '--grep=^git-svn-id:', '--date-order', '-1']
    
    DebugLog.print(str(cmd))
    output = subprocess.check_output(cmd).decode()
    m = re.search(r"git-svn-id: ([^@]*)@([0-9]*)", output)
    url = m.group(1)
    svn_rev = int(m.group(2))
    return (url, svn_rev)

def GetGitSvnUrl():
    output = subprocess.check_output(['git', 'config',  '--get', 'svn-remote.svn.url']).decode()
    output = output.splitlines()
    assert(len(output)==1)
    url = output[0]
    return url

@timeit
def GetSvnExternalsFromGitSvnBridge():
    hostRepoUrl = GetGitSvnUrl()

    # get all the svn:externals properties recursively
    cmd = ['git', 'svn',  'show-externals']
    out = subprocess.check_output(cmd).decode()

    # parse the output line by line fail in case or problems
    currentPathDef = ""
    externalDefinitions = []
    for line in out.splitlines():
        if len(line) ==0:
            continue

        DebugLog.print("Processing: " + line)
        if line.startswith("# /"):
            
            DebugLog.print("  -> currentPathDef: " + currentPathDef) 
            # key is a new pathDef
            currentPathDef = line[2:]
            continue
        
        # current line must be a externalDef
        externaldefString = line[len(currentPathDef):]
        DebugLog.print("  -> externaldefString: " + externaldefString)
        
        # derive windows  path from currentPathDef relative to repo root
        svnWCFolderPath = currentPathDef
        svnWCFolderPath = '.'+ svnWCFolderPath
        svnWCFolderPath.replace("/", os.sep)
        externaldef = svn.SvnExternal.parse(hostRepoUrl, svnWCFolderPath , externaldefString)
        externalDefinitions.append(externaldef)
    
    return externalDefinitions
