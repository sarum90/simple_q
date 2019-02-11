
from twisted.internet.defer import DeferredList
from twisted.trial import unittest

import server
import os

class ClientCalculationTestCase(unittest.TestCase):
  def setUp(self):
    address = 'localhost:8099'
    self.server = server.Server(address)

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

  def test_example(self):
    """Verify that the example given in the description works."""
    content = (
        'http://cuteoverload.files.wordpress.com/2014/10/unnamed23.jpg?'
        'w=750&h=1000')
    alice_subscription = self._VerifyStatus(
        self.server.POST('/kittens_and_puppies/alice'), 200)
    bob_subscription = self._VerifyStatus(
        self.server.POST('/kittens_and_puppies/bob'), 200)
    deferred = DeferredList([alice_subscription, bob_subscription])

    def CharlesPosting(unused_argument):
      charles_post = self._VerifyStatus(
          self.server.POST('/kittens_and_puppies', body=content), 200)
      return charles_post
    deferred.addCallback(CharlesPosting)

    def AliceSuccessfullyGetsPost(unused_argument):
      alice_get = self._VerifyStatusAndBody(
          self.server.GET('/kittens_and_puppies/alice'), 200, content)
      return alice_get
    deferred.addCallback(AliceSuccessfullyGetsPost)

    def AliceSeesNoPost(unused_argument):
      alice_get = self._VerifyStatus(
          self.server.GET('/kittens_and_puppies/alice'), 204)
      return alice_get
    deferred.addCallback(AliceSeesNoPost)

    def BobSuccessfullyGetsPost(unused_argument):
      bob_get = self._VerifyStatusAndBody(
          self.server.GET('/kittens_and_puppies/bob'), 200, content)
      return bob_get
    deferred.addCallback(BobSuccessfullyGetsPost)

    return deferred


