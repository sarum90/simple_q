from backends.memory import MemoryBackend

from twisted.trial import unittest

class MemoryBackendTest(unittest.TestCase):
  def setUp(self):
    self._backend = MemoryBackend()

  def _TotalMessageCount(self):
    """Test utility to count all messages in the backend."""
    return sum([len(v.messages) for _, v in self._backend._topics.iteritems()])

  def _Subscribe(self, topic, user):
    """Subscribe and verify that the operation worked."""
    self.assertEquals(200, self._backend.Subscribe(topic, user))

  def _PostMessage(self, topic, message):
    """Post a message and verify that the operation worked."""
    self.assertEquals(200, self._backend.PostMessage(topic, message))

  def test_basic(self):
    """Perform basic happy-case tests across the board."""
    self.assertEquals((404, None), self._backend.GetMessage('topic', 'user'))
    self._Subscribe('topic', 'user')
    self.assertEquals((204, None), self._backend.GetMessage('topic', 'user'))

    self.assertEquals(0, self._TotalMessageCount())
    self._PostMessage('topic', 'message')
    self.assertEquals(1, self._TotalMessageCount())

    self.assertEquals((200, 'message'),
                      self._backend.GetMessage('topic', 'user'))
    self.assertEquals(0, self._TotalMessageCount())
    self.assertEquals((204, None), self._backend.GetMessage('topic', 'user'))
    self.assertEquals(200, self._backend.Unsubscribe('topic', 'user'))
    self.assertEquals((404, None), self._backend.GetMessage('topic', 'user'))

  def test_unsubscribe_invalid_subscription(self):
    """Verify that Unsubscribe returns 404 on invalid subscriptions."""
    self.assertEquals(404, self._backend.Unsubscribe('topic', 'user'))

  def test_unsubscribe_removes_message_from_server(self):
    """Verify that a message will be removed if all subscribers unsubscribe."""
    self._Subscribe('topic', 'user')

    self.assertEquals(0, self._TotalMessageCount())
    self._PostMessage('topic', 'message')
    self.assertEquals(1, self._TotalMessageCount())
    self.assertEquals(200, self._backend.Unsubscribe('topic', 'user'))
    self.assertEquals(0, self._TotalMessageCount())

  def test_dont_get_message_if_subscribe_after_post(self):
    """Verify you do not get a message if you subscribe after it is posted."""
    self._PostMessage('topic', 'message1')
    self.assertEquals(0, self._TotalMessageCount())
    self._Subscribe('topic', 'user1')
    self.assertEquals((204, None), self._backend.GetMessage('topic', 'user1'))

    self._PostMessage('topic', 'message2')
    self._Subscribe('topic', 'user2')

    self.assertEquals((204, None), self._backend.GetMessage('topic', 'user2'))
    self.assertEquals(1, self._TotalMessageCount())
    self.assertEquals((200, 'message2'),
                      self._backend.GetMessage('topic', 'user1'))

    self.assertEquals(0, self._TotalMessageCount())

  def test_do_not_receive_messages_from_previous_subscription(self):
    """Verify that messages do not persist across an unsubscribe cycle."""
    self._Subscribe('topic', 'user1')
    self._Subscribe('topic', 'user2')
    self._PostMessage('topic', 'message')
    self.assertEquals(200, self._backend.Unsubscribe('topic', 'user1'))
    self._Subscribe('topic', 'user1')
    self.assertEquals((204, None), self._backend.GetMessage('topic', 'user1'))
    self.assertEquals((200, 'message'),
                      self._backend.GetMessage('topic', 'user2'))

