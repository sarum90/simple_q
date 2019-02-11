import server

from StringIO import StringIO

from mock import patch
from mock import ANY

from twisted.internet import reactor
from twisted.internet.defer import succeed
from twisted.internet.defer import Deferred
from twisted.internet.defer import DeferredList
from twisted.trial import unittest

class DummyResponse(object):
  def __init__(self, code):
    self.code = code

class ServerTest(unittest.TestCase):
  """Test for the server class.

  Unfortunately this class relies heavily on mocks to test the server. I think
  we have to assume the Twisted API works as specified and this is then the
  best we can do.
  """

  @patch('server.readBody')
  @patch('server.Agent')
  def test_request(self, mock_agent, mock_read_body):
    """Verify Request calls into Twisted as expected."""
    serv = server.Server('www.example.com')
    mock_agent.assert_called_with(reactor)
    agent_request_deferred = Deferred()
    mock_request = mock_agent.return_value.request
    mock_request.return_value = agent_request_deferred
    mock_read_body.return_value = succeed('body')

    d = serv.Request('METHOD', '/hihi/hi', body='MOUSE')

    mock_request.assert_called_with(
        'METHOD', 'http://www.example.com/hihi/hi', ANY, ANY)
    args, _ = mock_request.call_args
    _, _, _, body = args
    output = StringIO()
    body_deferred = body.startProducing(output)

    def VerifySentBody(unused_arg):
      self.assertEqual(output.getvalue(), 'MOUSE')
    body_deferred.addCallback(VerifySentBody)

    def VerifyResult(arg):
      status, body = arg
      self.assertEqual(body, 'body')
      self.assertEqual(status, 200)
    d.addCallback(VerifyResult)

    dl = DeferredList([body_deferred, d])
    # There is probably a better way to use DeferredLists to propagate errors,
    # but I did not come across it.
    def ProcessDeferredList(args):
      for success, error in args:
        if not success:
          raise error
    dl.addCallback(ProcessDeferredList)

    dummy_response = DummyResponse(200)
    agent_request_deferred.callback(dummy_response)
    return dl

