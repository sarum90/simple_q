import hashlib
import struct

def _HashToNumberLessThan(value, n):
  """Hashes value into an integer less than n, repeatable across platforms."""
  fmt = '<L'
  m = hashlib.md5()
  m.update(value)
  val = struct.unpack(fmt, m.digest()[:struct.calcsize(fmt)])[0]
  return val % n

class HashBackend(object):
  """This hash backend forwards requests to other backends based on topic"""

  def __init__(self, backends):
    """Simple constructor.

    Args:
      backends: A list of backends to forward requests to.
    """
    self._backends = backends

  def _GetBackendFor(self, topic):
    """Returns the correct backend for a given topic."""
    return self._backends[_HashToNumberLessThan(topic, len(self._backends))]

  def GetMessage(self, topic_name, user):
    """Retrieves the oldest message in topic_name that user has not gotten."""
    return self._GetBackendFor(topic_name).GetMessage(topic_name, user)
  
  def Subscribe(self, topic_name, user):
    """Subscribes user to topic_name."""
    return self._GetBackendFor(topic_name).Subscribe(topic_name, user)

  def PostMessage(self, topic_name, message):
    """Posts a message to topic_name."""
    return self._GetBackendFor(topic_name).PostMessage(topic_name, message)

  def Unsubscribe(self, topic_name, user):
    """Unsubscribes user from topic_name and clears pending messages."""
    return self._GetBackendFor(topic_name).Unsubscribe(topic_name, user)
