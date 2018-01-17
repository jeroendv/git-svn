a *simple* [git svn clone](https://git-scm.com/docs/git-svn) wrapper for use inside an existing svn checkout.

```
$ svn update                    # ensure clean svn working copy
$ git-svn-init                  # git clone
$ git-svn-migrateSvnIgnore      # migrate ignore rules
```

will 
1. create a git svn clone tracking the svn working copy from the BASE revision and onwards.
1. migrate all the svn ignore rules to git



# how to install

* clone this repo
* pip install ./

# one-time git svn clone

a specific revision can be specified
```
$ git-svn-init -r 1000
```

ignore specific svn folders in the git svn clone
```
$ git-svn-init --ignore-dir '3rd Party/' 'bigFiles/'
```

# daily git usage

to fetch the new svn commits into git

```
$ git svn fetch
```

rebase and linearize your branche on the SVN tracking branch head.
```
$ git svn rebase -l
```

rebuild git ignore rules from svn:ignore properties if they got updated.
```
$ git-svn-migrateSvnIgnore
```

To commit each commit of your active git branch to svn
```
$ git svn dcommit
```

# cave-ats
git svn is a git gateway drug. It allows devs to work locally in git while the backend is a svn repo. However it does have limitations.

* proven functionality for use in a a single branch creating new linear commits.

* However svn merging and svn branching should not be done through the git svn bridge. the git and svn concepts of merging and branching are to different, one *must* perform such actions in svn directly. And then fetch the result into the git repo using `git svn fetch`

* do not merge into the branch intended for pushing to svn! Always linearize your commis using the git rebase tools before calling `git svn dcommit`.





