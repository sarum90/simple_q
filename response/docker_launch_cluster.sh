
sudo docker build -t pubsub .

sudo docker run -d --name backend0 pubsub python clustered_backend.py
sudo docker run -d --name backend1 pubsub python clustered_backend.py
sudo docker run -d --name backend2 pubsub python clustered_backend.py
sudo docker run -d --name backend3 pubsub python clustered_backend.py

sudo docker run -d -p 8100:8080 --name frontend0 --link backend0:backend0 --link backend1:backend1 --link backend2:backend2 --link backend3:backend3 -e "NUM_BACKENDS=4" pubsub python clustered_frontend.py
sudo docker run -d -p 8101:8080 --name frontend1 --link backend0:backend0 --link backend1:backend1 --link backend2:backend2 --link backend3:backend3 -e "NUM_BACKENDS=4" pubsub python clustered_frontend.py
sudo docker run -d -p 8102:8080 --name frontend2 --link backend0:backend0 --link backend1:backend1 --link backend2:backend2 --link backend3:backend3 -e "NUM_BACKENDS=4" pubsub python clustered_frontend.py
sudo docker run -d -p 8103:8080 --name frontend3 --link backend0:backend0 --link backend1:backend1 --link backend2:backend2 --link backend3:backend3 -e "NUM_BACKENDS=4" pubsub python clustered_frontend.py
