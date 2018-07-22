import subprocess
from git_svn.debug import DebugLog
from git_svn import svn

def IsGitWc():
    try: 
        subprocess.check_output(['git', 'status'])
        return True
    except subprocess.CalledProcessError:
        return False


def IsGitWcDirty():
    text = subprocess.check_output(['git', 'status', "--short", '--untracked-files=no'])
    if len(text.splitlines()) == 0:
        return False
    else:
        return True

def IsGitSvnRepo():
    try: 
        subprocess.check_output(['git','svn', 'info'])
        return True
    except subprocess.CalledProcessError:
        return False


def GetCurrentGitBranch():
    output = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', '@']).decode()
    output = output.splitlines()
    assert len(output) == 1
    branchName = output[0]
    return branchName

def GitCountCommits(start, end):
    output = subprocess.check_output(['git', 'log' ,'--oneline', start + ".." + end]).decode()
    return len(output.splitlines())

def GetGitSvnBranchPointRev():
    # find the git commit where HEAD branched of from the SVN branch
    cmd =  ['git', 'log', '--grep=^git-svn-id:', '--first-parent', '-1', "--format=%H"]
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


def GetGitSvnUrl():
    output = subprocess.check_output(['git', 'config',  '--get', 'svn-remote.svn.url']).decode()
    output = output.splitlines()
    assert(len(output)==1)
    url = output[0]
    return url


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
        svnWCFolderPath.replace("/", "\\")
        externaldef = svn.SvnExternal.parse(hostRepoUrl, svnWCFolderPath , externaldefString)
        externalDefinitions.append(externaldef)
    
    return externalDefinitions
