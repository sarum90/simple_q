from StringIO import StringIO

from twisted.internet import reactor
from twisted.web.client import Agent, FileBodyProducer, readBody
from twisted.web.http_headers import Headers

class Server(object):
  """Simple utility for async HTTP queries to a host."""

  def __init__(self, host):
    """Basic constructor sets host and creates an agent."""
    self._host = host
    self._agent = Agent(reactor)

  def Request(self, method, endpoint, body=None):
    """Request a page from the server.
    
    This will make an http request to the server to the passed in endpoint
    using the passed in method. The optional body will also be transferred over
    http.
    
    Args:
      method: The HTTP method for the request.
      endpoint: The endpoint on the server to request.
      body: The optional body of the http request.
    """
    if body:
      body = FileBodyProducer(StringIO(body))
    d = self._agent.request(
        method,
        'http://%s%s' % (self._host, endpoint),
        Headers({'User-Agent': ['PubSub HTTP Client']}),
        body)

    def GetStatusAndBodyAsTuple(response):
      code = response.code
      d1 = readBody(response)
      d1.addCallback(lambda x: (code, x))
      return d1

    d.addCallback(GetStatusAndBodyAsTuple)
    return d

  def GET(self, *args, **kwargs):
    """Simple wrapper of Request for GET requests."""
    return self.Request('GET', *args, **kwargs)

  def POST(self, *args, **kwargs):
    """Simple wrapper of Request for POST requests."""
    return self.Request('POST', *args, **kwargs)

  def DELETE(self, *args, **kwargs):
    """Simple wrapper of Request for DELETE requests."""
    return self.Request('DELETE', *args, **kwargs)

