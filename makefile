server-transformer:
	pyenv local 3.7.4; \
	bash -c "source envs/MusicTransformer-tensorflow2.0/bin/activate ;\
		python server.py --module=MusicTransformer-tensorflow2.0 ;\
		deactivate"

server-remi:
	pyenv local 3.6.12; \
	bash -c "source envs/remi/bin/activate ;\
		python server.py --module=remi;\
		deactivate"

client:
	osc-repl server.yaml

envs:
	bash scripts/create-envs.sh

all: server
