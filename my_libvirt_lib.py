# vim: tabstop=4 shiftwidth=4 softtabstop=4
import libvirt,os,sys
from xml.etree import ElementTree

def get_devices(dom,path,devs):
	tree=ElementTree.fromstring(dom.XMLDesc(0))
	devices=[]
	for target in tree.findall(path):
		dev=target.get(devs)
		if not dev in devices:
			devices.append(dev)
	return devices
def daemonize(stdout='/dev/null', stderr=None, stdin='/dev/null',pidfile=None ):
       
	try:
		pid = os.fork()
		if pid > 0: sys.exit(0) 
	except OSError, e:
		sys.stderr.write("fork #1 failed: (%d) %s\n" % (e.errno, e.strerror))
		sys.exit(1)
	
	os.chdir("/")
	os.umask(0)
	os.setsid()

	try:
		pid = os.fork()
		if pid > 0: sys.exit(0) 
	except OSError, e:
		print 'second fork error'
		sys.stderr.write("fork #2 failed: (%d) %s\n" % (e.errno, e.strerror))
		sys.exit(1)
	if not stderr: stderr = stdout
	si = file(stdin, 'r')
	so = file(stdout, 'w')
	se = file(stderr, 'a+', 0)
	pid = str(os.getpid())
	print "Start with Pid: %s\n"  % pid
	sys.stderr.flush()
	if pidfile: file(pidfile,'w').write("%s\n" % pid)
	sys.stdout.flush()
	sys.stderr.flush()
	os.dup2(si.fileno(), sys.stdin.fileno())
	os.dup2(so.fileno(), sys.stdout.fileno())
	os.dup2(se.fileno(), sys.stderr.fileno())
