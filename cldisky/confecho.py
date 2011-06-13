import pkg_resources
import sys

file = open('/etc/cldisky.conf','w')
def main(out=sys.stdout):
    config = pkg_resources.resource_string(__name__, 'skel/sample.conf')
    out.write(config)
	file.write(config)
	file.close()


