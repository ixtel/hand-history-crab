"""runs all unittest modules in a directory.
	
modules to be recognized as unittests must have their name prefixed with "test_"
and must provide a "suit()" method returning the unittest.TestSuit for the module.

usage:
test_all.py [-d directory] [-r] [-v verbosity]

-d: (otional) directory to run unittests from - default is current directory
-r: (optional) run tests in directory recursively
-v: (optional) unittest output verbosity - integer 0-N

"""

import os, sys, unittest
#************************************************************************************
#
#************************************************************************************
DirSelf = os.path.abspath(os.path.dirname(__file__))

def main(directory=DirSelf, recursive=True, verbosity=2):
	
	runner = unittest.TextTestRunner(verbosity=verbosity)
	
	for root, dirs, files in os.walk(directory):
		for name in files:
			if not name.startswith('test_'): continue
			name, ext = os.path.splitext(name)
			if ext.lower() != '.py': continue
						
			sys.path.insert(0, root)
			module = __import__(name) 
			sys.path.pop(0)
			
			suite = getattr(module, 'suite', None)
			if suite is None: continue
			
			runner.run(suite())
			
		if not recursive:
			break
		
		
if __name__ == '__main__':
	import getopt
	optlist, args = getopt.getopt(sys.argv[1:], 'hrv:d:')
	d = dict(optlist)
	if '-h' in d:
		print __doc__
	else:
		kws = {
			'directory': d.get('-d', DirSelf),
			'recursive': True if '-r' in d else False,
			'verbosity': int(d.get('-v', 2)),
			}
		main(**kws)
	
	
