a set of convenience functions for  [git svn clone](https://git-scm.com/docs/git-svn) for the specific usecase of creating a git-svn bridge *inside* an existing svn checkout.

```
$ svn update                    # ensure clean svn working copy
$ git-svn-init                  # git clone
$ git-svn-migrateSvnIgnore      # migrate ignore rules
```

will 
1. create a git svn clone tracking the svn working copy from the BASE revision and onwards.
Relevant svn-bridge settings  like svn repo url, path, rev ... are automatically extracted from the svn working copy.
1. sensible git ignore rules based on svn
   * migrate svn:ignore properties
   * ignore .svn/ itself
   * ignore the svn externals
   * ignore the paths that git-svn bridge ignores itself



# how to install

requirements:
* git
* svn
* git-svn
* python

setup:
```
$ git clone <repo-url> 
$ cd git-svn
$ pip install ./
```

# Work flow


## one-time git svn clone

Create a git-svn bridge staring from a specific revision
```
$ git-svn-init -r 1000
```
see also `$ git-svn-init --help` for even more flags.

ignore specific svn folders in the git svn clone
```
$ git-svn-init --ignore-dir '3rd Party/' 'bigFiles/'
```
Note that this is reflected int he migrated svn ignore rules as well.

## daily git usage

use the regular [git svn commands](https://git-scm.com/docs/git-svn)

to fetch the new svn commits into git

```
$ git svn fetch
```

rebase and linearize your branche on the SVN tracking branch head.
```
$ git svn rebase -l
```

rebuild git ignore rules if needed.
```
$ git-svn-migrateSvnIgnore
```

To commit each commit of your active git branch to svn do
```
$ git svn dcommit
```

# cave-ats
git svn is a git gateway drug. It allows devs to work locally in git while the backend is a svn repo. However it does have limitations.

* proven functionality for use in a a single branch creating new linear commits.

* However svn merging and svn branching should not be done through the git svn bridge. the git and svn concepts of merging and branching are too different, one *must* perform such actions in svn directly. And then fetch the result into the git repo using `git svn fetch`

* do not merge into the branch intended for pushing to svn! Always linearize your commis using the git rebase tools before calling `git svn dcommit`.

# references
* official [git svn](https://git-scm.com/docs/git-svn) documentation





