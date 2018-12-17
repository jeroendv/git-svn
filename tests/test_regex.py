text = """commit dcddc9dea33c082bbc326da5c5d4542eb7c42d25
Author: PPereira <PPereira@cfd94225-6148-4c34-bb2a-21ea3148c527>
Date:   Mon Oct 22 14:15:34 2018 +0000

    creating Preview2DApp from development branch preview 2D testing applications

    git-svn-id: http://vsrv-bele-svn1/svn/Software/Main/NMAPI/NMAPI_Main@72028 cfd94225-6148-4c34-bb2a-21ea3148c527
"""

import re

def test_regex():
    m = re.search(r"git-svn-id: ([^@]*)@([0-9]*)", text)
    assert m
    assert 2 == len(m.groups())
    assert "http://vsrv-bele-svn1/svn/Software/Main/NMAPI/NMAPI_Main" == m.group(1)
    assert "72028" == m.group(2)

