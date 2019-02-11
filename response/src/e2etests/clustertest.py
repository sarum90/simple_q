from twisted.internet.defer import DeferredList
from twisted.trial import unittest

import server

class ClusterTestCases(unittest.TestCase):
  def setUp(self):
    """Set up assuming that "start_cluster.sh" has been run."""
    self._servers = [server.Server('localhost:8100'),
                     server.Server('localhost:8101'),
                     server.Server('localhost:8102'),
                     server.Server('localhost:8103')]

  def _VerifyStatus(self, deferred_request, status):
    """Asserts that the deferred_request finishes with the given status."""

    def VerifyStatus(response):
      response_status, _ = response
      self.assertEqual(response_status, status)
    
    deferred_request.addCallback(VerifyStatus)
    return deferred_request

  def _VerifyStatusAndBody(self, deferred_request, status, body):
    """Asserts that the deferred_request has the given status and body."""

    def VerifyStatusAndBody(response):
      response_status, response_body = response
      self.assertEqual(response_status, status)
      self.assertEqual(response_body, body)
    
    deferred_request.addCallback(VerifyStatusAndBody)
    return deferred_request

  def _RunExampleTest(self, server_func, topic='kittens_and_puppies'):
    """Verify that the example given in the description on all servers."""
    content = (
        'http://cuteoverload.files.wordpress.com/2014/10/unnamed23.jpg?'
        'w=750&h=1000')

    alice_subscription = self._VerifyStatus(
        server_func().POST('/%s/alice' % topic), 200)
    bob_subscription = self._VerifyStatus(
        server_func().POST('/%s/bob' % topic), 200)
    deferred = DeferredList([alice_subscription, bob_subscription])

    def CharlesPosting(unused_argument):
      charles_post = self._VerifyStatus(
          server_func().POST('/%s' % topic, body=content), 200)
      return charles_post
    deferred.addCallback(CharlesPosting)

    def AliceSuccessfullyGetsPost(unused_argument):
      alice_get = self._VerifyStatusAndBody(
          server_func().GET('/%s/alice' % topic), 200, content)
      return alice_get
    deferred.addCallback(AliceSuccessfullyGetsPost)

    def AliceSeesNoPost(unused_argument):
      alice_get = self._VerifyStatus(
          server_func().GET('/%s/alice' % topic), 204)
      return alice_get
    deferred.addCallback(AliceSeesNoPost)

    def BobSuccessfullyGetsPost(unused_argument):
      bob_get = self._VerifyStatusAndBody(
          server_func().GET('/%s/bob' % topic), 200, content)
      return bob_get
    deferred.addCallback(BobSuccessfullyGetsPost)

    return deferred

  def test_server_1(self):
    """Verify that the first frontend can run the example."""
    return self._RunExampleTest(lambda: self._servers[0])

  def test_server_2(self):
    """Verify that the second frontend can run the example."""
    return self._RunExampleTest(lambda: self._servers[1])

  def test_server_3(self):
    """Verify that the third frontend can run the example."""
    return self._RunExampleTest(lambda: self._servers[2])

  def test_server_4(self):
    """Verify that the fourth frontend can run the example."""
    return self._RunExampleTest(lambda: self._servers[3])

  def test_across_frontends(self):
    """Verify the example passes if you hit all the frontends.""" 
    servers = {'current': 0}
    def NextServer():
      servers['current'] = (servers['current'] + 1) % len(self._servers)
      return self._servers[servers['current']]
    return self._RunExampleTest(NextServer)

  def test_across_frontends_and_topics(self):
    """This tests across topics simultaniously and hits all the frontends.

    Note that this test can take a bit of time if the servers are logging to
    stdout.
    """
    servers = {'current': 0}
    def NextServer():
      servers['current'] = (servers['current'] + 1) % len(self._servers)
      return self._servers[servers['current']]

    deferreds = []
    for i in xrange(50):
      topic = str(i)
      deferreds.append(self._RunExampleTest(NextServer, topic=topic))

    dl = DeferredList(deferreds)
    # There is probably a better way to use DeferredLists to propagate errors,
    # but I did not come across it.
    def ProcessDeferredList(args):
      for success, error in args:
        if not success:
          raise error
    dl.addCallback(ProcessDeferredList)

    return dl
