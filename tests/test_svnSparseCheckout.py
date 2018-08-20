import pytest
import yaml


def test_yamlConfigLoading():
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

def test_yamlConfigLoadingFromFile():
    with open('.svnSparseConfig', "wt") as f:
        f.write("""svnRepoUrl: http://myserver.com/svn/aPath
files:
    - file1.txt
    - afolder/fileInaFolder.log
""")

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


def test_SvnSparseCheckoutInvocation():
    from git_svn.SvnSparseCheckout import main

    with open('.svnSparseCheckout.yml', "wt") as f:
        f.write("""svnRepoUrl: http://myserver.com/svn/aPath
files:
    - file1.txt
    - afolder/fileInaFolder.log
""")

    # recipy to load yaml from file
    main()




