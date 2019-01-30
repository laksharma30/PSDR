from __future__ import print_function
import numpy as np

from psdr import BoxDomain, TensorProductDomain, UniformDomain, Function



class OAS(Function):
	def __init__(self):
		domain = build_oas_design_domain() * build_oas_robust_domain() * build_oas_random_domain()
		Function.__init__(self, oas_func, domain, vectorized = True)


def build_oas_design_domain(n_cp = 3):
	# Twist
	domain_twist = BoxDomain(-1*np.ones(n_cp), 1*np.ones(n_cp))
	# Thick
	domain_thick = BoxDomain(0.005*np.ones(n_cp), 0.05*np.ones(n_cp))
	# Root Chord
	domain_root_chord = BoxDomain(0.7, 1.3)
	# Taper ratio
	domain_taper_ratio = BoxDomain(0.75, 1.25)

	return TensorProductDomain([domain_twist, domain_thick, domain_root_chord, domain_taper_ratio])

def build_oas_robust_domain():
	# alpha - Angle of Attack
	return BoxDomain(2.0, 5.0)

def build_oas_random_domain():
	E = UniformDomain(0.8*70e9, 1.2*70e9)	 
	G = UniformDomain(0.8*30e9, 1.2*30e9)
	rho = UniformDomain(0.8*3e3, 1.2*3e3)
	return TensorProductDomain([E,G,rho])


def oas_func(x, version = 'v1', workdir = None, verbose = True):
	r"""



	"""
	# If we use this inside the RedisPool, we need to load the modules
	# internal to this file
	import shutil, subprocess, os, tempfile, shlex, platform
	import numpy as np
	from subprocess import Popen, PIPE, STDOUT

	if workdir is None:
		# Docker cannot access /var by default, so we move the temporary file to
		# /tmp on MacOS
		if platform.system() == 'Darwin':
			workdir = tempfile.mkdtemp(dir = '/tmp')
		else:
			workdir = tempfile.mkdtemp()
	else:
		workdir = os.path.abspath(workdir)
		os.makedirs(workdir)

	# Copy the inputs to a file
	np.savetxt(workdir + '/my.input', x, fmt = '%.15e')
	
	call = "docker run -t --rm --mount type=bind,source='%s',target='/workdir' jeffreyhokanson/oas:%s /workdir/my.input" % (workdir, version)
	args = shlex.split(call)
	with open(workdir + '/output.log', 'a') as log:
		p = Popen(args, stdout = PIPE, stderr = STDOUT)
		while True:
			# Read output from pipe
			# TODO: this should buffer to end of line rather than fixed size
			output = p.stdout.readline()
			log.write(output)

			if verbose:
				print(output, end ='')

			# Check for termination
			if p.poll() is not None:
				break
		if p.returncode != 0:
			print("exited with error code %d" % p.returncode)

	Y = np.loadtxt(workdir + '/my.output')

	#shutil.rmtree(workdir) 
	return Y	
	



if __name__ == '__main__':
	oas = OAS()
	X = oas.sample(10)
	Y = oas(X)	
	print(Y)
