
export NUM_BACKENDS=4
export BACKEND0_PORT=tcp://localhost:8110
export BACKEND1_PORT=tcp://localhost:8111
export BACKEND2_PORT=tcp://localhost:8112
export BACKEND3_PORT=tcp://localhost:8113


KILLLINE=""
export PORT=8110 && python clustered_backend.py &
P=$!
echo "Launched backend pid: $P"
KILLLINE="$KILLLINE $P"
export PORT=8111 && python clustered_backend.py &
P=$!
echo "Launched backend pid: $P"
KILLLINE="$KILLLINE $P"
export PORT=8112 && python clustered_backend.py &
P=$!
KILLLINE="$KILLLINE $P"
echo "Launched backend pid: $P"
export PORT=8113 && python clustered_backend.py &
P=$!
KILLLINE="$KILLLINE $P"
echo "Launched backend pid: $P"

export PORT=8100 && python clustered_frontend.py &
P=$!
KILLLINE="$KILLLINE $P"
echo "Launched frontend pid: $P"
export PORT=8101 && python clustered_frontend.py &
P=$!
KILLLINE="$KILLLINE $P"
echo "Launched frontend pid: $P"
export PORT=8102 && python clustered_frontend.py &
P=$!
KILLLINE="$KILLLINE $P"
echo "Launched frontend pid: $P"
export PORT=8103 && python clustered_frontend.py &
P=$!
KILLLINE="$KILLLINE $P"
echo "Launched frontend pid: $P"

read -rsp $'Press any key to continue...\n' -n1 key

for K in $KILLLINE; do
  echo "killing $K"
  kill $K
done
