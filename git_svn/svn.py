from git_svn.debug import DebugLog
import os
import subprocess
import urllib.parse
from xml.etree import ElementTree as ET
import shutil

def IsSvnWcDirty(path = "."):
    try: 
        text = subprocess.check_output(['svn', 'status', '--quiet', path])
        if len(text.splitlines()) == 0:
            return False
        else:
            return True
    except:
        raise

def IsSvnWc(path = "."):
    try: 
        subprocess.check_output(['svn', 'info', path])
        return True
    except subprocess.CalledProcessError:
        return False


def SvnCountCommits(startRev, endRev):
    cmd = ["svn", "log", "--xml", "-r", str(startRev) + ":" + str(endRev)]
    DebugLog.print(str(cmd))
    xmlStr = subprocess.check_output(cmd).decode()   
    xmlNode = ET.fromstring(xmlStr)
    return len(xmlNode.findall('logentry'))

def checkout(rev_int):
    subprocess.check_call(['svn', 'update','-r', str(rev_int)])


class SvnExternal:
    """ Single svn:external definition set on a specific folder in a working copy
    [-r <operativeRev>] <url>[@<pegRev>] <path>

    see also: http://svnbook.red-bean.com/en/1.7/svn.advanced.externals.html
    """
    @property
    def QualifiedUrl(self):
        """return a qualified url scheme://netloc/path from the external url
        based on the repoRoot url and the svn external definition url
        """
        if self.url.startswith("../"):
            raise NotImplementedError()
        elif self.url.startswith("^/../"):
            raise NotImplementedError()
        elif self.url.startswith("^/"):
            # relative to repo root url
            hostRepoUrl = self.hostRepoUrl
            # ensure that the hostRepoUrl is a folder, not a file
            # e.g. end with a folder separator.
            if not hostRepoUrl.endswith('/'):
                hostRepoUrl = hostRepoUrl + '/'

            relativeUrl = self.url[2:]
            return urllib.parse.urljoin(hostRepoUrl, relativeUrl)
        elif self.url.startswith("//"):
            # relative to server scheme
            repourl = urllib.parse.urlparse(self.hostRepoUrl)
            externalurl = urllib.parse.urlparse(self.url)
            return urllib.parse.urlunparse((repourl.scheme,
                                            externalurl.netloc,
                                            externalurl.path,
                                            "", "", ""))
        elif self.url.startswith("/"):
            # relative to server root url
            url = urllib.parse.urlparse(self.hostRepoUrl)
            return urllib.parse.urlunparse((url.scheme,
                                            url.netloc,
                                            self.url,
                                            "", "", ""))
        else:
            return self.url

    def __init__(self,  hostRepoUrl, svnWCFolderPath, operativeRev, url, pegRev, path):
        self.hostRepoUrl = hostRepoUrl
        self.svnWCFolderPath = svnWCFolderPath
        self.path = path
        self.url = url
        self.pegRev = pegRev
        self.operativeRev = operativeRev

    def __str__(self):
        __str = ""
        if self.operativeRev is not None:
            __str += "-r " + str(self.operativeRev) + " "

        __str += self.url

        if self.pegRev is not None:
            __str += '@' + str(self.pegRev)

        __str += " " + self.path
        return __str

    @staticmethod
    def parse(hostRepoUrl, svnWCFolderPath, definition):
        """Create a SvnExternal instance given a single svn:externals definition
        [-r <operativeRev>] <url>[@<pegRev>] <path>
        """

        DebugLog.print("parsing: " + str(definition))
    
        remainder = definition
        # parse operative Revision
        terms = remainder.split(' ')
        if terms[0] == '-r':
            operativeRev = terms[1]
            remainder = " ".join(terms[2:])
            del terms
        else:
            operativeRev = None
            del terms

        # parse url & peg revision
        terms = remainder.split(' ')
        PegSeparatorIdx = terms[0].find('@')
        if PegSeparatorIdx == -1:
            url = terms[0]
            pegRev = None

            remainder = " ".join(terms[1:])
        else:
            url = terms[0][:PegSeparatorIdx]
            pegRev = terms[0][(PegSeparatorIdx+1):]

            remainder = " ".join(terms[1:])
        del terms

        # parse path
        assert(len(remainder) > 0)
        path = remainder
        if path[0] == "'" and path[-1] == "'":
            path = path[1:-1]

        return SvnExternal(hostRepoUrl, svnWCFolderPath, operativeRev, url, pegRev, path)

def GetQualifiedUrlForFolder(path):
    xmlStr = subprocess.check_output(['svn', 'info', '--xml', path]).decode()
    xmlRootNode = ET.fromstring(xmlStr)
    return xmlRootNode.find('entry/url').text


def checkoutSvnExternal(svnExternal):
    """checkout or update an svn external
    """
    WCExternalPath = os.path.join(svnExternal.svnWCFolderPath, svnExternal.path.replace('/', os.sep))


    # check for existing svn external pointing to wrong url
    # in which case the external needs to be deleted and a clean checkout is needed
    # instead of only updating the existing svnExternal to the proper revision
    if os.path.exists(WCExternalPath):

        # an svn working copy is expected!
        if not IsSvnWc(WCExternalPath):
            raise Exception("Terminating: svn external expected, but no svn WC is found:" + WCExternalPath)

        # svn wc may not be dirty, since this action would result in lost data!
        if IsSvnWcDirty(WCExternalPath):
            raise Exception("Terminating: dirty svn external can't be removed : " + WCExternalPath)

        # if the working copy is a checkout of the wrong svn url then delete it.
        # e.g. the external has updated and  new checkout is needed
        existingExternalQualifiedUrl = GetQualifiedUrlForFolder(WCExternalPath)
        forceCleanCheckout = (svnExternal.QualifiedUrl != existingExternalQualifiedUrl)
        # if the pegRev and operatative revision are set but not equal, then lets be conservative and do a clean checkout.
        forceCleanCheckout |= ((svnExternal.operativeRev is not None) and (svnExternal.pegRev != svnExternal.operativeRev))
        if forceCleanCheckout:
            DebugLog.print('removing {path}!\n existing external points to {oldUrl} but new external points to {newUrl}. so a new checkout is needed.'.format(
                path=WCExternalPath,
                oldUrl=existingExternalQualifiedUrl,
                newUrl=svnExternal.QualifiedUrl
            ))
            shutil.rmtree(WCExternalPath)


    if os.path.isdir(WCExternalPath):
        # build svn cli arguments
        cmd  = ['svn', 'up', '-q'] 
        if svnExternal.pegRev:
            assert (svnExternal.operativeRev is None) or (svnExternal.operativeRev == svnExternal.pegRev)
            cmd += ['-r', str(svnExternal.pegRev)]
        
        cmd += ['.']


        # checkout already exists, just update it
        pwd = os.getcwd()
        os.chdir(WCExternalPath)
        try:
            DebugLog.print(str(cmd))
            svnOutput = subprocess.check_output(cmd).decode()
            DebugLog.print(svnOutput)
        finally:
            os.chdir(pwd)
    elif os.path.isfile(WCExternalPath):
        # build svn cli arguments
        cmd = ['svn', 'up', '-q']
        if svnExternal.pegRev:
            assert (svnExternal.operativeRev is None) or (svnExternal.operativeRev == svnExternal.pegRev)
            cmd += ['-r', str(svnExternal.pegRev)]
        
        cmd += [os.path.basename(WCExternalPath)]


        # checkout already exists, just update it
        pwd = os.getcwd()
        os.chdir(os.path.dirname(WCExternalPath))
        try:
            DebugLog.print(str(cmd))
            svnOutput = subprocess.check_output(cmd).decode()
            DebugLog.print(svnOutput)
        finally:
            os.chdir(pwd)

    else:
        assert not os.path.exists(WCExternalPath)
        # build svn cli arguments
        cmd = ['svn', 'checkout', '-q']
        if svnExternal.operativeRev:
            cmd += ['-r', str(svnExternal.operativeRev)]
        
        if svnExternal.pegRev:
            cmd += [svnExternal.QualifiedUrl+'@'+str(svnExternal.pegRev)]
        else:
            cmd += [svnExternal.QualifiedUrl]

        cmd += [svnExternal.path.replace('/', os.sep)]
        
        # external doesn't yet exists, check it out from the svn repo
        pwd = os.getcwd()
        os.makedirs(svnExternal.svnWCFolderPath, exist_ok=True)
        os.chdir(svnExternal.svnWCFolderPath)
        try:
            DebugLog.print(str(cmd))
            svnOutput = subprocess.check_output(cmd).decode()
            DebugLog.print(svnOutput)
        finally:
            os.chdir(pwd)

def GetSvnWCBaseRev():
    xmlStr = subprocess.check_output(['svn', 'info' ,'--xml', '-r',  'BASE']).decode()
    xmlEl = ET.fromstring(xmlStr)
    return xmlEl.find('entry').get('revision')

def GetSvnRepoUrl():
    xmlStr = subprocess.check_output(['svn', 'info',  '--xml', '']).decode()
    xmlEl = ET.fromstring(xmlStr)
    repoUrl = xmlEl.find('entry/repository/root').text
    return repoUrl

def GetSvnExternalsFromLocalSvnWc():
    hostRepoUrl = GetSvnRepoUrl()

    # get all the svn:externals properties recursively
    cmd = ["svn", "pget", "svn:externals", '-R', './']
    out = subprocess.check_output(cmd).decode()

    # parse the output line by line fail in case or problems
    currentPathDef = ""
    externalDefinitions = []
    for line in out.splitlines():
        if len(line) ==0:
            continue

        if " - " in line:
            (key, sep, value) = line.partition(' - ')
            assert sep == ' - '

            # key is a new pathDef
            currentPathDef = key
            assert key[0] != '/'
            currentPathDef = currentPathDef

            # value if first externalDef for pathDef
            externaldef = SvnExternal.parse(hostRepoUrl, currentPathDef,value)
            externalDefinitions.append(externaldef)
            continue
        
        # current line must be a externalDef
        externaldef = SvnExternal.parse(hostRepoUrl, currentPathDef, line)
        externalDefinitions.append(externaldef)
    
    return externalDefinitions
	
