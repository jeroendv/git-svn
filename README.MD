
# how to install

* clone this repo
* pip install ./

# create a git repor

```
$ git-svn-init
$ git-svn-migrateSvnIgnore
```

# git usage

to fetch the svn branch into git

```
$ git svn fetch
```

rebase and linearize your branche on the new svn  HEAD

```
$ git svn rebase -l
```

To commit your branch to git
```
$ git svn dcommit
```


