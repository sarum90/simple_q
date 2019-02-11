# PubSub Server

This directory contains Marcus Ewert's (sarum90@gmail.com) completion of the
programming excercise that is part of the hiring process for ClusterHQ.

# Approach

In the interest of constructing production software I approached this problem
looking for designs that would scale well. To that end, this problem is easily
sharded by topic, as any interactions with 1 topic have no effect on other
topics. To exploit this, I did a simple frontend/backend design for the service
where the front ends handle any requests made to them and route them to backends
hashed on topic. This would theoretically scale out until a single topic was so
popular that it required multiple backends to process requests for it. This
seemed like a reasonable limit for the scope of the exercise.

I tried to keep the design modular so that I could test each part individually.
The modular design also made it easy to whip up a single server python script
for a lighter weight version of the clustered solution.

The last question was where to store the actual subscription and message data.
Given the note that, "Messages need not persist across server restarts" I went
for the fairly straightforward implementation of just storing this data in
python structures in memory. Unfortunately with my implementation even
subscription data is lost on server restarts. In practice it probably makes more
sense to store subscriptions in a database and perhaps messages on a redis
server. I've tried to keep my design modular enough that it would not be too
much work to put something like that in place, but for my 1 day implementation
I've used a simple python in-memory backing store.

# Dependencies

Python is my strongest language for writing quick HTTP servers, and I decided to
take this opportunity to learn what Twisted is all about. The nature of writing
deferred-based async code was reminiscent of some of my recent hobby coding in
JavaScript with Promises, and I found it fun to work with the Twisted library.

I also depend on the python mock library because it enables some very powerful
quick unit tests.

# Structure

The general approach is there is a file named `frontend.py` that handles all of
the HTTP status code generation and url parsing. This then calls into some
backend that has the API implemented in python. The actual frontend nodes will
call into a hashing backend that will forward the command to a proxying backend
based on topic hash. The proxying backend will connect to the backend node,
which is simply just frontend.py connected to the in memory implementation of a
backend.

In approximate ASCII-Art form the cluster looks like the following:

                                                     __________________________
                                                  ->|       Backend            |
                   Similar Frontends attached    /  |__________________________|
                   to the same Backends...      | ->|       Backend            |
              _________________________________ //  |__________________________|
             |         Frontend     ->proxy.py +/   |       Backend            |
             |                     /->proxy.py +    |                          |
    User --->|fronend.py -> hash.py-->proxy.py + -> | frontend.py -> memory.py |
             |_________________________________|    |__________________________|

# Manifest (src/)

- backends/hash.py - Backend that hashes topic and forward to another backend.
- backends/memory.py - In memory python implementation of the backend.
- backends/proxy.py - Backend that connects over HTTP to another server.
- backends/test_hash.py - Unit tests for hash.py.
- backends/test_memory.py - Unit tests for memory.py.
- backends/test_proxy.py - Unit tests for proxy.py.
- frontend.py - HTTP handling and url parsing.
- test_frontend.py - Unit tests for frontend.py.
- server.py - Utility for being an HTTP client of a server (test, proxy.py).
- test_server.py - Unit tests for server.py
- clustered_backend.py - Configured startup script for cluster backends.
- clustered_frontend.py - Configured startup script for cluster frontends.
- e2etests/basic.py - Simple e2e test of basic functionality.
- e2etests/clustertest.py - Slightly more involved test for clustered solution.
- Makefile - Makefile filled with a couple shortcuts
- start_cluster.sh - non-docker way of starting a cluster

# Testing

## Unit Tests

When writing production services I like to ensure unit test coverage of all
parts of the production code. Along all of the production code in my src
directory (`foo.py`) you should find a corresponding test (`test_foo.py`). There
is a target in the Makefile that I used to quickly run all of these unit tests
with `trial` as some of them are async Twisted tests.

## End to end tests

There are also two simple end to end tests. I did not develop a whole bunch of
infrastructure around running them, but they can be run against running
instances of the service, and verify that the standard example given in the
instructions pass. To verify the clustered solution they even intentionally
round-robin schedule to different frontends and simultaneously launch many
requests at once.

# How to run:

In actually launching a production system you would want to have some sort of
cluster manager available to verify the service is running, restart it if it
crashes, alert you if it is down for too long, etc.

I did the work to be able to set up a cluster in docker, which seemed to me to
be a reasonable stopping point for the scope if the exercise. Below are the
instructions for both how to start up a single process version of my solution,
and an 8 process clustered solution using docker.

Note that in the cluster scenario, I would envision a load-balancer in front of
the 4 frontends (Or DNS round robin, etc.). The configuration of which I have
left outside of my submission.

## Single server manually (twisted python module must be installed -- pip install -r requirements.txt):

cd src/
python frontend.py

## Single server via docker:
    ./docker_launch_single.sh # Starts server on port 8099

### Corresponding tests (mock and twisted python modules required -- pip install -r dev-requirements.txt):

    cd src && PYTHONPATH="${PWD}" trial e2etests/basic.py

## Clustered server via docker:
    ./docker_launch_cluster.sh # Starts frontends on ports 8100, 8101, 8102, and 8103

### Corresponding tests (mock and twisted python modules required -- pip install -r dev-requirements.txt):

    cd src && PYTHONPATH="${PWD}" trial e2etests/clustertest.py

# Logging

In debugging production systems it is vital to have good logging. In
development, I added the logging that I believe would be useful for debugging
(and added unit tests to verify it was working), but I did not do the work to
actually place the logs somewhere useful. I would envision using something like
[loggly](https://www.loggly.com/docs/python-http/) and taking some time to set
up log aggregating with a service. This would be useful for aggregating data on
usage and alerting on 500s as well.

# Metrics

Additionally, for production systems we would want standard CPU usage / memory usage and latency metrics for aggregation + alerting so that we can detect when the system is unhealthy, requiring additional sharding, performance optimizations, or a re-design to accommodate large topics.
