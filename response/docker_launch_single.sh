
sudo docker build -t pubsub .

sudo docker run -d -p 8099:8080 --name singleserver pubsub python frontend.py
