
UNIT_TESTS=test_server.py \
					 test_frontend.py \
	 			   backends/test_hash.py \
           backends/test_memory.py \
           backends/test_proxy.py

test:
	PYTHONPATH="${PWD}" trial $(UNIT_TESTS)

single_e2etest:
	PYTHONPATH="${PWD}" trial e2etests/basic.py

cluster_e2etest:
	PYTHONPATH="${PWD}" trial e2etests/clustertest.py
