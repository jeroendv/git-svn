a set of convenience functions for  [git svn clone](https://git-scm.com/docs/git-svn)
for the specific usecase of creating a git-svn bridge *inside* an existing svn checkout.

Typical use-case is a situation where a regular `git svn clone` would not suffice.
Due to svn-externals, scripts that assumes a svn working copy to be present,
svn:keywords or SubWCRev usages, ...

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
([official Info](https://git-scm.com/docs/git-svn#_rebase_vs_pull_merge))
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


## periodiccaly
ocasionally the svn working copy must be updated.
* perform a merge. (git-svn bridge doesn't do this!)
* update the svn-externals (git-svn bridge has no support for externals)
* ...

First make sure that your git working copy is clean, e.g. no local changes.
This way all work is backed up and any mistake can easily be reverted.

figure out the svn commit that is currently being tracked by the git-bridge working copy
```
$ git svn info
```

then update svn to said revision and revert all conflicts that may happen.
```
$ svn up -r XXXXXX
$ svn revert -R ./
```
At the and both the git and svn working copy should be clean and clear of any local changes.

# cave-ats
git svn is a git gateway drug. It allows devs to work locally in git while the backend is a svn repo. However it does have limitations.

* proven functionality for use in a a single branch creating new linear commits.

* However svn merging and svn branching should not be done through the git svn bridge. the git and svn concepts of merging and branching are too different, one *must* perform such actions in svn directly. And then fetch the result into the git repo using `git svn fetch`

* do not merge into the branch intended for pushing to svn! Always linearize your commis using the git rebase tools before calling `git svn dcommit`.

# references
official git-svn documentation:
* [cli reference](https://git-scm.com/docs/git-svn)
* [additional docs](https://git-scm.com/docs/git-svn#_rebase_vs_pull_merge)))
* [caveats](https://git-scm.com/docs/git-svn#_caveats)
* [bugs](https://git-scm.com/docs/git-svn#_bugs)




