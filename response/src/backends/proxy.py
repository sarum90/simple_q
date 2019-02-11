from server import Server

class ProxyBackend(object):
  """This backend simply proxies the request to another service."""

  def __init__(self, host):
    """Constructor.

    Args:
      host: The host to proxy requests to (i.e. www.example.com).
    """
    self._server = Server(host)

  def GetMessage(self, topic_name, user):
    """Retrieves the oldest message in topic_name that user has not gotten."""
    return self._server.GET('/%s/%s' % (topic_name, user))

  def PostMessage(self, topic_name, message):
    """Posts a message to topic_name."""
    d = self._server.POST('/%s' % topic_name, body=message)

    def ExtractStatus(args):
      status, _ = args
      return status
    d.addCallback(ExtractStatus)

    return d

  def Subscribe(self, topic_name, user):
    """Subscribes user to topic_name."""
    d = self._server.POST('/%s/%s' % (topic_name, user))
    def ExtractStatus(args):
      status, _ = args
      return status
    d.addCallback(ExtractStatus)

    return d

  def Unsubscribe(self, topic_name, user):
    """Unsubscribes user from topic_name and clears pending messages."""
    d = self._server.DELETE('/%s/%s' % (topic_name, user))
    def ExtractStatus(args):
      status, _ = args
      return status
    d.addCallback(ExtractStatus)

    return d
