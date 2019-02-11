
class _Message(object):
  """A simple message structure for the in-memory backend."""
  def __init__(self, users, message):
    self.subs = set(users)
    self.message = message

  def Delivered(self):
    """Whether this message has been delivered to all subscribers."""
    return self.subs == set()

  def __repr__(self):
    return '[%s %s]' % (self.subs, self.message)

class _Topic(object):
  """A simple topic class for the in-memory backend."""
  def __init__(self):
    self.subs = set()  # Current subscribers.
    # TODO: If perf is needed, change this to be a deque.
    self.messages = []  # Pending messages.

class MemoryBackend(object):
  """An in-memory backend for the pubsub server.

  Everything here is syncronous, so we do not have to worry about locking.
  """

  def __init__(self):
    self._topics = {}

  def GetTopic(self, topic_name):
    """Retrieves the requested topic, potentially creating it if need be."""
    if topic_name not in self._topics:
      self._topics[topic_name] = _Topic()
    return self._topics[topic_name]

  def GetMessage(self, topic_name, user):
    """Retrieves the oldest message in topic_name that user has not gotten."""
    topic = self.GetTopic(topic_name)
    retval = None
    index = -1
    if user not in topic.subs:
      return 404, None
    for i, m in enumerate(topic.messages):
      if user in m.subs:
        m.subs.remove(user)
        if m.Delivered():
          topic.messages.pop(i)
        return 200, m.message
    return 204, None

  def Subscribe(self, topic_name, user):
    """Subscribes user to topic_name."""
    self.GetTopic(topic_name).subs.add(user)
    return 200

  def PostMessage(self, topic_name, message):
    """Posts a message to topic_name."""
    topic = self.GetTopic(topic_name)
    if topic.subs != set():
      topic.messages.append(_Message(topic.subs, message))
    return 200

  def Unsubscribe(self, topic_name, user):
    """Unsubscribes user from topic_name and clears pending messages."""
    topic = self.GetTopic(topic_name)
    if user in topic.subs:
      for m in topic.messages:
        m.subs.remove(user)
      topic.messages = [m for m in topic.messages if not m.Delivered()]
      topic.subs.remove(user)
      return 200
    return 404
