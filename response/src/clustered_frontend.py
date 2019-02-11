import os

from backends.proxy import ProxyBackend
from backends.hash import HashBackend
from frontend import RunServer

if __name__ == '__main__':
  backends = []
  for i in xrange(int(os.environ['NUM_BACKENDS'])):
    key = os.environ['BACKEND%d_PORT' % i]
    address = key.split('//')[1]
    backends.append(ProxyBackend(address))
  RunServer(HashBackend(backends), int(os.environ['PORT']))

