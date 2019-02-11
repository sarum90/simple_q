# Tests for the fronend. Verifies that the HTTP aspects of the API are handled
# correctly, and mocks out the backends to ensure that the frontend forwards to
# the backends appropriately.

from frontend import PubSubResource

from mock import MagicMock
from mock import patch

from twisted.trial import unittest
from twisted.internet.defer import succeed
from twisted.internet.defer import Deferred
from twisted.web.server import NOT_DONE_YET
from twisted.web.test.test_web import DummyRequest

class DummyContentProvider(object):
  """Dummy implementation of request.content."""

  def __init__(self, content):
    self._content = content

  def read(self):
    return self._content

class DummyRequestWithContent(DummyRequest):
  def __init__(self, endpoint_array, body):
    super(DummyRequestWithContent, self).__init__(endpoint_array)
    self.content = DummyContentProvider(body)
    

def _Render(resource, request):
  """Renders a request using a resource yeilding a deferred."""
  result = resource.render(request)
  if isinstance(result, str):
    request.write(result)
    request.finish()
    return succeed(None)
  elif result is NOT_DONE_YET:
    if request.finished:
      return succeed(None)
    else:
      return request.notifyFinish()
  else:
    raise ValueError("Unexpected return value: %r" % (result,))

def _RenderToDeferredStatusBody(resource, request):
  """Renders a given request using the given resource.

  The resulting deferred finishes with a tuple (status_code, result_body).

  Args:
    resource: The Resource to use to render the request.
    request: The request to render.

  Returns:
    A deferred that will conclude with a (status_code, response_body) tuple.
  """
  d = _Render(resource, request)
  
  def GetStatusAndBody(unused_arg):
    return (request.responseCode, "".join(request.written))
  d.addCallback(GetStatusAndBody)
  return d

class FrontendTest(unittest.TestCase):
  def setUp(self):
    """Sets up the mock backend and creates the resource to be tested."""
    self._mock_backend = MagicMock()
    self._pubSubResource = PubSubResource(self._mock_backend)
    self._request = None

  def _CreateDummyRequest(self, method, endpoint, body=None):
    """Created a request object for the specified parameters."""
    request = DummyRequestWithContent(endpoint.split('/'), body)
    request.method = method
    # TODO: body
    self._request = request
    return request
      
  def _Request(self, method, endpoint, body=None):
    """Executes an HTTP request returns a deferred."""
    request = self._CreateDummyRequest(method, endpoint, body=body)
    return _RenderToDeferredStatusBody(self._pubSubResource, request)

  def _TestEndpoint(self, async, method, endpoint, expected_response_status,
                    expected_response_body=None,
                    backend_method_mock=None, body=None,
                    backend_method_return_value=None,
                    backend_method_error=None,
                    expected_backend_method_args=None):
    """Highly paramaterized test wrapper.

    This method can be used to run a full test against an endpoint verifying
    return status and body. It is designed to just execute 1 HTTP request, mock
    out the backend response, and then verify the results.
    
    Args:
      async: Whether the backend is async or sync.
      method: The HTTP method to use (i.e. 'POST').
      endpoint: The HTTP path to query.
      expected_response_status: The expected status of the HTTP response.
      expected_response_body: The expected body of the HTTP response.
      backend_method_mock: A mock in the backend that is expected to be hit.
      body: The body of the request to the resource.
      backend_method_return_value: The value the backend method should return.
      backend_method_error: The error that the backend method should raise.
      expected_backend_method_args: The expected argument to the backend call.

    Returns:
      A deferred that will complete when the processing is complete.
    """
    backend_method_deferred = Deferred()
    if backend_method_mock:
      if async:
        backend_method_mock.return_value = backend_method_deferred
      else:
        if backend_method_return_value:
          backend_method_mock.return_value = backend_method_return_value
        if backend_method_error:
          backend_method_mock.side_effect = backend_method_error
    d = self._Request(method, endpoint, body=body)

    def VerifyResult(response_status_and_body):
      status, body = response_status_and_body
      self.assertEqual(status, expected_response_status)
      if expected_response_body is not None:
        self.assertEqual(body, expected_response_body)
      if backend_method_mock and expected_backend_method_args:
        backend_method_mock.assert_called_with(*expected_backend_method_args)
    d.addCallback(VerifyResult)

    if async:
      self.assertFalse(
          self._request.finished, 'Finished before async backend returned.')
      if backend_method_return_value:
        backend_method_deferred.callback(backend_method_return_value)
      if backend_method_error:
        backend_method_deferred.errback(backend_method_error)
    return d
    
  def test_sync_subscribe(self):
    """Verify subscribe works with syncronous backends."""
    return self._TestEndpoint(
      async=False,
      method='POST',
      endpoint='test_topic/test_user',
      expected_backend_method_args=['test_topic', 'test_user'],
      backend_method_mock=self._mock_backend.Subscribe,
      backend_method_return_value=1234,
      expected_response_status=1234)

  def test_async_subscribe(self):
    """Verify subscribe works with asyncronous backends."""
    return self._TestEndpoint(
      async=True,
      method='POST',
      endpoint='test_topic/test_user',
      expected_backend_method_args=['test_topic', 'test_user'],
      backend_method_mock=self._mock_backend.Subscribe,
      backend_method_return_value=1234,
      expected_response_status=1234)

  @patch('frontend.logging.info')
  @patch('frontend.time.time')
  def test_subscribe_logging(self, mock_time, mock_log):
    """Verify subscribe logs meaningful data."""
    times = [10, 1]
    def fake_time():
      if not times:
        self.fail('Called time.time() too many times')
      return times.pop()
    mock_time.side_effect = fake_time

    d = self._TestEndpoint(
      async=False,
      method='POST',
      endpoint='test_topic/test_user',
      expected_backend_method_args=['test_topic', 'test_user'],
      backend_method_mock=self._mock_backend.Subscribe,
      backend_method_return_value=4321,
      expected_response_status=4321)

    def VerifyResult(unused_argument):
      args, _ = mock_log.call_args
      logline = args[0] % args[1:]
      self.assertIn("4321", logline)
      self.assertIn("9000ms", logline)
      self.assertIn("test_topic", logline)
      self.assertIn("test_user", logline)

    d.addCallback(VerifyResult)
    return d

  @patch('frontend.logging.info')
  @patch('frontend.logging.error')
  def _TestSubscribeLoggingErrors(self, async, mock_log_error, mock_log_info):
    """Verify subscribe logs meaningful data on 500s."""
    d = self._TestEndpoint(
      async=async,
      method='POST',
      endpoint='test_topic/test_user',
      expected_backend_method_args=['test_topic', 'test_user'],
      backend_method_mock=self._mock_backend.Subscribe,
      backend_method_error=Exception("Except"),
      expected_response_status=500)

    def VerifyResult(unused_argument):
      args, _ = mock_log_info.call_args
      logline = args[0] % args[1:]
      self.assertIn("500", logline)
      self.assertIn("Subscribe", logline)
      self.assertTrue(mock_log_error.called)

    d.addCallback(VerifyResult)
    return d

  def test_subscribe_logging_errors_sync(self):
    """Verify subscribe logs meaningful data on 500s with sync backend."""
    self._TestSubscribeLoggingErrors(False)

  def test_subscribe_logging_errors_async(self):
    """Verify subscribe logs meaningful data on 500s with async backend."""
    self._TestSubscribeLoggingErrors(True)

  def test_sync_postmessage(self):
    """Verify postmessage works with syncronous backends."""
    return self._TestEndpoint(
      async=False,
      method='POST',
      endpoint='test_topic',
      body='MESSAGE',
      expected_backend_method_args=['test_topic', 'MESSAGE'],
      backend_method_mock=self._mock_backend.PostMessage,
      backend_method_return_value=1234,
      expected_response_status=1234)

  def test_async_postmessage(self):
    """Verify postmessage works with asyncronous backends."""
    return self._TestEndpoint(
      async=True,
      method='POST',
      endpoint='test_topic',
      body='MESSAGE',
      expected_backend_method_args=['test_topic', 'MESSAGE'],
      backend_method_mock=self._mock_backend.PostMessage,
      backend_method_return_value=1234,
      expected_response_status=1234)

  @patch('frontend.logging.info')
  @patch('frontend.time.time')
  def test_postmessage_logging(self, mock_time, mock_log):
    """Verify post message logs meaningful data."""
    times = [10, 1]
    def fake_time():
      if not times:
        self.fail('Called time.time() too many times')
      return times.pop()
    mock_time.side_effect = fake_time

    d = self._TestEndpoint(
      async=False,
      method='POST',
      endpoint='test_topic',
      body='MESSAGE',
      expected_backend_method_args=['test_topic', 'MESSAGE'],
      backend_method_mock=self._mock_backend.PostMessage,
      backend_method_return_value=4321,
      expected_response_status=4321)

    def VerifyResult(unused_argument):
      args, _ = mock_log.call_args
      logline = args[0] % args[1:]
      self.assertIn("4321", logline)
      self.assertIn("9000ms", logline)
      self.assertIn("PostMessage", logline)
      self.assertIn("test_topic", logline)
      self.assertIn("MESSAGE", logline)

    d.addCallback(VerifyResult)
    return d

  @patch('frontend.logging.info')
  @patch('frontend.logging.error')
  def _TestPostMessageLogErrors(self, async, mock_log_error, mock_log_info):
    """Verify postmessage logs meaningful data on 500s."""
    d = self._TestEndpoint(
      async=async,
      method='POST',
      endpoint='test_topic',
      body='MESSAGE',
      expected_backend_method_args=['test_topic', 'MESSAGE'],
      backend_method_mock=self._mock_backend.PostMessage,
      backend_method_error=Exception("Except"),
      expected_response_status=500)

    def VerifyResult(unused_argument):
      args, _ = mock_log_info.call_args
      logline = args[0] % args[1:]
      self.assertIn("500", logline)
      self.assertIn("PostMessage", logline)
      self.assertTrue(mock_log_error.called)

    d.addCallback(VerifyResult)
    return d

  def test_postmessage_logging_errors_sync(self):
    """Verify postmessage logs meaningful data on 500s with sync backends."""
    return self._TestPostMessageLogErrors(False)

  def test_postmessage_logging_errors_async(self):
    """Verify postmessage logs meaningful data on 500s with async backends."""
    return self._TestPostMessageLogErrors(True)

  def test_post_bad_endpoint(self):
    """Verify that posting to endpoints with more than 2 '/'s is a 404."""
    return self._TestEndpoint(
      async=False,
      method='POST',
      endpoint='test_topic/test_user/fun_for_all',
      expected_response_status=404)

  def test_sync_getmessage(self):
    """Verify getmessage works with syncronous backends."""
    return self._TestEndpoint(
      async=False,
      method='GET',
      endpoint='test_topic/test_user',
      expected_backend_method_args=['test_topic', 'test_user'],
      backend_method_mock=self._mock_backend.GetMessage,
      backend_method_return_value=(1234, 'MESSAGE'),
      expected_response_status=1234, 
      expected_response_body='MESSAGE')

  def test_async_getmessage(self):
    """Verify getmessage works with asyncronous backends."""
    return self._TestEndpoint(
      async=True,
      method='GET',
      endpoint='test_topic/test_user',
      expected_backend_method_args=['test_topic', 'test_user'],
      backend_method_mock=self._mock_backend.GetMessage,
      backend_method_return_value=(1234, 'MESSAGE'),
      expected_response_status=1234, 
      expected_response_body='MESSAGE')

  @patch('frontend.logging.info')
  @patch('frontend.time.time')
  def test_getmessage_logging(self, mock_time, mock_log):
    """Verify getmessage logs meaningful data."""
    times = [10, 1]
    def fake_time():
      if not times:
        self.fail('Called time.time() too many times')
      return times.pop()
    mock_time.side_effect = fake_time

    d = self._TestEndpoint(
      async=False,
      method='GET',
      endpoint='test_topic/test_user',
      expected_backend_method_args=['test_topic', 'test_user'],
      backend_method_mock=self._mock_backend.GetMessage,
      backend_method_return_value=(4321, 'MESSAGE'),
      expected_response_status=4321,
      expected_response_body='MESSAGE')

    def VerifyResult(unused_argument):
      args, _ = mock_log.call_args
      logline = args[0] % args[1:]
      self.assertIn("4321", logline)
      self.assertIn("9000ms", logline)
      self.assertIn("GetMessage", logline)
      self.assertIn("test_topic", logline)
      self.assertIn("test_user", logline)
      self.assertIn("MESSAGE", logline)

    d.addCallback(VerifyResult)
    return d

  @patch('frontend.logging.info')
  @patch('frontend.logging.error')
  def _TestGetMessageLogErrors(self, async, mock_log_error, mock_log_info):
    """Verify getmessage logs meaningful data on 500s."""
    d = self._TestEndpoint(
      async=async,
      method='GET',
      endpoint='test_topic/test_user',
      expected_backend_method_args=['test_topic', 'test_user'],
      backend_method_mock=self._mock_backend.GetMessage,
      backend_method_error=Exception("Except"),
      expected_response_status=500)

    def VerifyResult(unused_argument):
      args, _ = mock_log_info.call_args
      logline = args[0] % args[1:]
      self.assertIn("500", logline)
      self.assertIn("GetMessage", logline)
      self.assertTrue(mock_log_error.called)

    d.addCallback(VerifyResult)
    return d

  def test_getmessage_logging_errors_sync(self):
    """Verify getmessage logs meaningful data on 500s with sync backends."""
    return self._TestGetMessageLogErrors(False)

  def test_getmessage_logging_errors_async(self):
    """Verify getmessage logs meaningful data on 500s with async backends."""
    return self._TestGetMessageLogErrors(True)

  def test_get_bad_endpoint_long(self):
    """Verify that getting endpoints with more than 2 '/'s is a 404."""
    return self._TestEndpoint(
      async=False,
      method='GET',
      endpoint='test_topic/test_user/fun_for_all',
      expected_response_status=404)

  def test_get_bad_endpoint_short(self):
    """Verify that getting endpoints with less than 1 '/'s is a 404."""
    return self._TestEndpoint(
      async=False,
      method='GET',
      endpoint='test_topic',
      expected_response_status=404)

  def test_sync_unsubscribe(self):
    """Verify unsubscribe works with syncronous backends."""
    return self._TestEndpoint(
      async=False,
      method='DELETE',
      endpoint='test_topic/test_user',
      expected_backend_method_args=['test_topic', 'test_user'],
      backend_method_mock=self._mock_backend.Unsubscribe,
      backend_method_return_value=1234,
      expected_response_status=1234)

  def test_async_unsubscribe(self):
    """Verify unsubscribe works with asyncronous backends."""
    return self._TestEndpoint(
      async=True,
      method='DELETE',
      endpoint='test_topic/test_user',
      expected_backend_method_args=['test_topic', 'test_user'],
      backend_method_mock=self._mock_backend.Unsubscribe,
      backend_method_return_value=1234,
      expected_response_status=1234)

  @patch('frontend.logging.info')
  @patch('frontend.time.time')
  def test_unsubscribe_logging(self, mock_time, mock_log):
    """Verify unsubscribe logs meaningful data."""
    times = [10, 1]
    def fake_time():
      if not times:
        self.fail('Called time.time() too many times')
      return times.pop()
    mock_time.side_effect = fake_time

    d = self._TestEndpoint(
      async=False,
      method='DELETE',
      endpoint='test_topic/test_user',
      expected_backend_method_args=['test_topic', 'test_user'],
      backend_method_mock=self._mock_backend.Unsubscribe,
      backend_method_return_value=4321,
      expected_response_status=4321)

    def VerifyResult(unused_argument):
      args, _ = mock_log.call_args
      logline = args[0] % args[1:]
      self.assertIn("4321", logline)
      self.assertIn("9000ms", logline)
      self.assertIn("Unsubscribe", logline)
      self.assertIn("test_topic", logline)
      self.assertIn("test_user", logline)

    d.addCallback(VerifyResult)
    return d

  @patch('frontend.logging.info')
  @patch('frontend.logging.error')
  def _TestUnsubscribeLogErrors(self, async, mock_log_error, mock_log_info):
    """Verify unsubscribe logs meaningful data on 500s."""
    d = self._TestEndpoint(
      async=async,
      method='DELETE',
      endpoint='test_topic/test_user',
      expected_backend_method_args=['test_topic', 'test_user'],
      backend_method_mock=self._mock_backend.Unsubscribe,
      backend_method_error=Exception("Except"),
      expected_response_status=500)

    def VerifyResult(unused_argument):
      args, _ = mock_log_info.call_args
      logline = args[0] % args[1:]
      self.assertIn("500", logline)
      self.assertIn("Unsubscribe", logline)
      self.assertTrue(mock_log_error.called)

    d.addCallback(VerifyResult)
    return d

  def test_unsubscribe_logging_errors_sync(self):
    """Verify unsubscribe logs meaningful data on 500s with sync backends."""
    return self._TestUnsubscribeLogErrors(False)

  def test_unsubscribe_logging_errors_async(self):
    """Verify unsubscribe logs meaningful data on 500s with async backends."""
    return self._TestUnsubscribeLogErrors(True)

  def test_delete_bad_endpoint_long(self):
    """Verify that deleting endpoints with more than 2 '/'s is a 404."""
    return self._TestEndpoint(
      async=False,
      method='DELETE',
      endpoint='test_topic/test_user/fun_for_all',
      expected_response_status=404)

  def test_delete_bad_endpoint_short(self):
    """Verify that deleting endpoints with less than 1 '/'s is a 404."""
    return self._TestEndpoint(
      async=False,
      method='DELETE',
      endpoint='test_topic',
      expected_response_status=404)

