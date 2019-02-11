import os

from backends.memory import MemoryBackend
from frontend import RunServer

if __name__ == '__main__':
  RunServer(MemoryBackend(), int(os.environ['PORT']))

