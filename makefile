server-transformer:
	pyenv local 3.7.4; \
	source envs/MusicTransformer-tensorflow2.0/bin/activate ;\
	python server.py ;\
	deactivate

server-remi:
	pyenv local 3.6.12; \
	source envs/remi/bin/activate ;\
	python server.py ;\
	deactivate

client:
	osc-repl server.yaml

envs:
	bash scripts/create-envs.sh

all: server
