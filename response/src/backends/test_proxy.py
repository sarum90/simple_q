from backends import proxy

from mock import patch

from twisted.trial import unittest
from twisted.internet.defer import succeed

class ProxyBackendTest(unittest.TestCase):
  @patch('backends.proxy.Server')
  def setUp(self, mock_server):
    self._proxy = proxy.ProxyBackend('cat')
    mock_server.assert_called_with('cat')
    self._mock_server = mock_server.return_value

  def test_get_message(self):
    """Verify GetMessage forwards to the correct endpoint."""
    self._mock_server.GET.return_value = succeed((200, 'body'))
    d = self._proxy.GetMessage('topic', 'user')
    self._mock_server.GET.assert_called_with('/topic/user')

    def VerifyResult(arg):
      self.assertEqual(arg, (200, 'body'))
    d.addCallback(VerifyResult)

    return d

  def test_post_message(self):
    """Verify PostMessage forwards to the correct endpoint."""
    self._mock_server.POST.return_value = succeed((200, ''))
    d = self._proxy.PostMessage('topic', 'message')
    self._mock_server.POST.assert_called_with('/topic', body='message')

    def VerifyResult(arg):
      self.assertEqual(arg, 200)
    d.addCallback(VerifyResult)

    return d

  def test_subscribe(self):
    """Verify Subscribe forwards to the correct endpoint."""
    self._mock_server.POST.return_value = succeed((200, ''))
    d = self._proxy.Subscribe('topic', 'user')
    self._mock_server.POST.assert_called_with('/topic/user')

    def VerifyResult(arg):
      self.assertEqual(arg, 200)
    d.addCallback(VerifyResult)

    return d

  def test_unsubscribe(self):
    """Verify Unsubscribe forwards to the correct endpoint."""
    self._mock_server.DELETE.return_value = succeed((200, ''))
    d = self._proxy.Unsubscribe('topic', 'user')
    self._mock_server.DELETE.assert_called_with('/topic/user')

    def VerifyResult(arg):
      self.assertEqual(arg, 200)
    d.addCallback(VerifyResult)

    return d
