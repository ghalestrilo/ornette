server-transformer:
	

server-melody_rnn:
	./start.sh server-melody_rnn

client:
	./start.sh client

envs:
	bash scripts/create-envs.sh

all: server
