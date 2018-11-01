import pytest
import yaml
import os
import sys

def test_yamlConfigLoading(tmpdir):
    yamlStr="""svn-repo-url: http://myserver.com/svn/aPath
files:
    - file1.txt
    - afolder/fileInaFolder.log
"""
    yamlConfig = yaml.load(yamlStr)
    print(yamlConfig)

    # yamlConfig is a dictionary with 2 notes
    assert yamlConfig['svn-repo-url']  == "http://myserver.com/svn/aPath"
    assert 2 == len(yamlConfig['files'])

    # the files node is a list with 2 ellements
    assert 'file1.txt' == yamlConfig['files'][0]
    assert 'afolder/fileInaFolder.log' == yamlConfig['files'][1]

def test_yamlConfigLoadingFromFile(tmpdir):
    os.chdir(tmpdir)
    with open('.svnSparseCheckout.yml', "wt") as f:
        f.write("""svnRepoUrl: http://myserver.com/svn/aPath
files:
    - file1.txt
    - afolder/fileInaFolder.log
""")
    print("tmpdir: " + str(tmpdir) + "\n")
    print("cwd: " + str(os.getcwd()) + "\n")

    # recipy to load yaml from file
    with open('.svnSparseCheckout.yml', 'rt') as f2:
        yamlConfig = yaml.load(f2)
        print(yamlConfig)


    # yamlConfig is a dictionary with 2 notes
    assert yamlConfig['svnRepoUrl']  == "http://myserver.com/svn/aPath"
    assert 2 == len(yamlConfig['files'])

    # the files node is a list with 2 ellements
    assert 'file1.txt' == yamlConfig['files'][0]
    assert 'afolder/fileInaFolder.log' == yamlConfig['files'][1]


def test_SvnSparseCheckoutInvocation(tmpdir):
    os.chdir(tmpdir)
    with open('.svnSparseCheckout.yml', "wt") as f:
        f.write("""svnRepoUrl: http://myserver.com/svn/aPath
files:
    - file1.txt
    - afolder/fileInaFolder.log
""")

    
    # recipy to load yaml from file
    sys.argv = ['scriptname', '--dry-run', '--debug']
    import git_svn.SvnSparseCheckout
    git_svn.SvnSparseCheckout.main()




