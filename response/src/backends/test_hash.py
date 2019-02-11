from backends.hash import HashBackend
from backends.hash import _HashToNumberLessThan

from mock import MagicMock
from twisted.trial import unittest

class MemoryBackendTest(unittest.TestCase):
  def setUp(self):
    self._backends = [MagicMock(), MagicMock(), MagicMock()]
    self._backend = HashBackend(self._backends)

  def test_hash_number_less_than(self):
    """Verify that _HashToNumberLessThan works as expected."""
    for val in ['cat', 'mousey', 'dogdog', 'ASDFASDF']:
      for cap in [2, 3, 5, 200]:
        v = _HashToNumberLessThan(val, cap)
        self.assertEqual(v, _HashToNumberLessThan(val, cap),
                         'Hash not repeatable.')
        self.assertGreaterEqual(v, 0)
        self.assertLess(v, cap)

  def test_get_backend_for(self):
    """Verify that _GetBackendFor always returns one of the backends."""
    for topic in ['cats', 'kittens', 'bunnies', 'apricots']:
      self.assertIn(self._backend._GetBackendFor(topic), self._backends)

    backends = set()
    for topic in xrange(500):
      backend = self._backend._GetBackendFor(str(topic))
      self.assertIn(backend, self._backends)
      backends.add(backend)
    # For 500 topics at random we should see more than just 1 backend.
    self.assertGreater(len(backends), 1)

  def test_get_message(self):
    """Verify that GetMessage is forwarded correctly."""
    self._backend._GetBackendFor('topic').GetMessage.return_value = 'PIE'
    self.assertEquals('PIE', self._backend.GetMessage('topic', 'user'))
    self._backend._GetBackendFor('topic').GetMessage.assert_called_with(
        'topic', 'user')

  def test_post_message(self):
    """Verify that PostMessage is forwarded correctly."""
    self._backend._GetBackendFor('ooo').PostMessage.return_value = '00'
    self.assertEquals('00', self._backend.PostMessage('ooo', 'user'))
    self._backend._GetBackendFor('ooo').PostMessage.assert_called_with(
        'ooo', 'user')

  def test_subscribe(self):
    """Verify that Subscribe is forwarded correctly."""
    self._backend._GetBackendFor('cipot').Subscribe.return_value = 'APE'
    self.assertEquals('APE', self._backend.Subscribe('cipot', 'user'))
    self._backend._GetBackendFor('cipot').Subscribe.assert_called_with(
        'cipot', 'user')

  def test_unsubscribe(self):
    """Verify that Unsubscribe is forwarded correctly."""
    self._backend._GetBackendFor('ttttt').Unsubscribe.return_value = '777'
    self.assertEquals('777', self._backend.Unsubscribe('ttttt', 'user'))
    self._backend._GetBackendFor('ttttt').Unsubscribe.assert_called_with(
        'ttttt', 'user')


