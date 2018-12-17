import pytest
import sys
import os
import subprocess
from  git_svn.gitSvnDefInit import *

def test_parseConfig1(tmpdir):
    config ="""url: http://foobar/
branches:
    - trunk
"""
    git_svn_def = git.GitSvnDef.parseConfig(config)
    # check the url
    assert git_svn_def.url == "http://foobar/"

    # check that there is one branch
    assert git_svn_def.branches == ["trunk"]

def test_parseConfig1(tmpdir):
    config ="""url: http://foobar/
branches:
    - trunk
    - branches/v1.0
"""
    git_svn_def = GitSvnDef.parseConfig(config)
    # check the url
    assert git_svn_def.url == "http://foobar/"

    # check that there are 2 branches
    assert set(git_svn_def.branches) == set(["branches/v1.0", "trunk"])

def test_parseConfig2(tmpdir):
    """Test parsing a config with an 'ignore-paths' list key
    """
    config="""url: http://vsrv-bele-svn1.mtrs.intl/svn/Software
branches:
    - Main/Focus/Focus_Main
    - Production/Focus/Focus_11.8.4
    - Production/Focus/Focus_11.9.1
ignore-paths:
    - packages/
    - Source/libraries/Packages/"""

    git_svn_def = GitSvnDef.parseConfig(config)
    
    assert git_svn_def.ignore_paths == set(['packages/', 'Source/libraries/Packages/'])



def test_parseConfig_errorReporting():
    with pytest.raises(Exception):
        config = ""
        git.GitSvnDef.parseConfig(config)

    with pytest.raises(Exception):
        config = "url: foobar"
        git.GitSvnDef.parseConfig(config)

    with pytest.raises(Exception):
        config = """url: http://foobar
branches: foobar
"""
        git.GitSvnDef.parseConfig(config)
    


# def test_cli(tmpdir):
#     os.chdir(tmpdir)
#     print("cwd: "+ str(os.getcwd()))
#     with open('.gitsvn.yml', "wt") as f:
#         f.write("""url: http://foobar/
# branches:
#     - trunk
# """)

#     subprocess.check_call(['git', 'init'])
    
#     # recipy to load yaml from file
#     sys.argv = ['scriptname', '--debug', '-N']
#     import git_svn.gitSvnDefInit 
#     git_svn.gitSvnDefInit.main()

import sys
if __name__ == '__main__':
    pytest.main(sys.argv)