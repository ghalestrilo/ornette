# Ornette base image
FROM elixir


WORKDIR /engine
COPY . /engine

RUN mix local.hex --force
RUN mix deps.get
RUN mix deps.compile

CMD mix start