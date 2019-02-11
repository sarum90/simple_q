
import logging
import time
import os
import errno

from twisted.internet import reactor
from twisted.internet.task import deferLater
from twisted.internet.defer import maybeDeferred
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET
from twisted.web.server import Site

from backends.memory import MemoryBackend

def _FormatTime(start):
  """Logging utility that returns string of time since start with units."""
  time_in_ms = 1000*(time.time() - start)
  return '%dms' % int(time_in_ms)

class PubSubResource(Resource):
  """The resource that provides the perscribed HTTP endpoints."""
  isLeaf=True

  def __init__(self, backend):
    """Basic constructor for PubSubResource."""
    self._backend = backend

  def _FailureCallback(self, request, start, logstring):
    """Generates a simple errback handler for deferred http requests."""
    def FailureCallback(err):
      request.setResponseCode(500)
      request.write('')
      request.finish()
      logging.error(err)
      logging.info('500 %s %s', _FormatTime(start), logstring)
    return FailureCallback

  def _GetNextMessage(self, topic, user, request):
    """Wraps the backend GetNextMessage with HTTP protocol to the client."""
    d = maybeDeferred(self._backend.GetMessage, topic, user)
    start = time.time()
    logstring = 'GetMessage (%s, %s)' % (topic, user)
    def FinishGetNextMessage(arg):
      code, body = arg
      body = body or ''
      logging.info('%d %s %s %s', code, _FormatTime(start), logstring, body)
      request.setResponseCode(code)
      request.write(body)
      request.finish()
    d.addCallback(FinishGetNextMessage)
    d.addErrback(self._FailureCallback(request, start, logstring))

  def _Subscribe(self, topic, user, request):
    """Wraps the backend Subscribe with HTTP protocol to the client."""
    d = maybeDeferred(self._backend.Subscribe, topic, user)
    start = time.time()
    logstring = 'Subscribe (%s, %s)' % (topic, user)
    def FinishSubscribe(code):
      logging.info('%d %s %s', code, _FormatTime(start), logstring)
      request.setResponseCode(code)
      request.write('')
      request.finish()
    d.addCallback(FinishSubscribe)
    d.addErrback(self._FailureCallback(request, start, logstring))

  def _Unsubscribe(self, topic, user, request):
    """Wraps the backend Subscribe with HTTP protocol to the client."""
    d = maybeDeferred(self._backend.Unsubscribe, topic, user)
    start = time.time()
    logstring = 'Unsubscribe (%s, %s)' % (topic, user)
    def FinishUnubscribe(code):
      logging.info('%d %s %s', code, _FormatTime(start), logstring)
      request.setResponseCode(code)
      request.write('')
      request.finish()
    d.addCallback(FinishUnubscribe)
    d.addErrback(self._FailureCallback(request, start, logstring))

  def _PostMessage(self, topic, message, request):
    """Wraps the backend PostMessage with HTTP protocol to the client."""
    d = maybeDeferred(self._backend.PostMessage, topic, message)
    start = time.time()
    logstring = 'PostMessage (%s, %s)' % (topic, message)
    def FinishPostMessage(code):
      logging.info('%d %s %s',
          code, _FormatTime(start), logstring)
      request.setResponseCode(code)
      request.write('')
      request.finish()
    d.addCallback(FinishPostMessage)
    d.addErrback(self._FailureCallback(request, start, logstring))

  def render_DELETE(self, request):
    """Verifies the format of the request path and routes for DELETE calls."""
    if len(request.postpath) == 2:
      topic, user = request.postpath
      self._Unsubscribe(topic, user, request)
      return NOT_DONE_YET
    request.setResponseCode(404)
    return ''

  def render_POST(self, request):
    """Verifies the format of the request path and routes for POST calls."""
    if len(request.postpath) == 1:
      topic = request.postpath[0]
      message = request.content.read()
      self._PostMessage(topic, message, request)
      return NOT_DONE_YET
    elif len(request.postpath) == 2:
      topic, user = request.postpath
      self._Subscribe(topic, user, request)
      return NOT_DONE_YET
    request.setResponseCode(404)
    return ''

  def render_GET(self, request):
    """Verifies the format of the request path and routes for GET calls."""
    if len(request.postpath) == 2:
      topic, user = request.postpath
      self._GetNextMessage(topic, user, request)
      return NOT_DONE_YET
    request.setResponseCode(404)
    return ''

def RunServer(backend, port):
  # Logging set up to go to a directory, for easy debugging of clustered
  # server.
  try:
    os.mkdir('logs')
  except OSError as exc:
    if exc.errno == errno.EEXIST:
      pass
    else:
      raise
  logging.basicConfig(filename=os.path.join('logs', 'server-%d.log' % port),
                      level=logging.DEBUG)
  resource = PubSubResource(backend)
  factory = Site(resource)
  reactor.listenTCP(port, factory)
  reactor.run()

if __name__ == '__main__':
  RunServer(MemoryBackend(), 8080)
