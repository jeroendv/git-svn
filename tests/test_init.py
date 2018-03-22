import pytest
import os
from git_svn.init import *

from xml.etree import ElementTree as ET

xml = """<?xml version="1.0" encoding="UTF-8"?>
<info>
<entry
   kind="dir"
   path="."
   revision="59693">
<url>http://source-be.mtrs.intl/svn/focus/Main/Shared/Shared_Main/libraries</url>
<relative-url>^/Main/Shared/Shared_Main/libraries</relative-url>
<repository>
<root>http://source-be.mtrs.intl/svn/focus</root>
<uuid>cfd94225-6148-4c34-bb2a-21ea3148c527</uuid>
</repository>
<wc-info>
<wcroot-abspath>D:/dev/Libraries/main/Shared_Main</wcroot-abspath>
<schedule>normal</schedule>
<depth>infinity</depth>
</wc-info>
<commit
   revision="59007">
<author>paulo_pereira</author>
<date>2017-11-24T14:38:21.310740Z</date>
</commit>
</entry>
</info>
"""

def test_parse_SVN_info():

    info_root = ET.fromstring(xml)
    n = info_root.findall("./entry/repository/root")
    assert 1 == len(n)
    root_url = n[0].text
    assert "http://source-be.mtrs.intl/svn/focus" == root_url

    n = info_root.findall("./entry/relative-url")
    assert 1 == len(n)
    relative_url = n[0].text
    assert "^/Main/Shared/Shared_Main/libraries" == relative_url

    n = info_root.findall('./entry/commit')
    assert 1 == len(n)
    rev = int(n[0].get('revision'))
    assert 59007 == rev


    assert "libraries" == os.path.basename(relative_url)




if __name__ == '__main__':
    pytest.main()
