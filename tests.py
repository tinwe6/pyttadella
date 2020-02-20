"""
Use pytest to execute the tests

If you use the --pdb option, pytest will stop when an assertion fails and leave
you in a debugger prompt.

env PYTHONPATH=. pytest --pdb
"""

from utils import Version
def test_version():
    code = 1026
    vers = Version.from_code(code)
    assert str(vers) == "0.4.2"
    assert vers.major == 0 and vers.minor == 4 and vers.sublvl == 2
    assert vers.code == code

from commands import test_bx

def make_tests():
	s = "Ciao {1} !"
	print(s.format("bello", "brutto"))
	test_version()
	test_bx()
	print('all tests passed')
	#exit(0)
