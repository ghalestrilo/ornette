FROM debian:buster

ENV LANG=C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive

ENV SC_VERSION=3.10.4
ENV SCP_VERSION=3.10.0

RUN apt-get update -y -q && \
    apt-get install -y -q apt-utils && \
    apt-get dist-upgrade -y -q && \
    groupadd tidal -g 1000 && \
    useradd tidal -g 1000 -u 1000 -m -G audio

RUN apt-get install -y -q \
    build-essential \
    bzip2 \
    ca-certificates \
    cmake \
    curl \
    git \
    jackd2 \
    libasound2-dev \
    libavahi-client-dev \
    libcwiid-dev \
    libffi-dev \
    libfftw3-dev \
    libgmp-dev \
    libicu-dev \
    libjack-jackd2-dev \
    libncurses-dev \
    libreadline6-dev \
    libsndfile1-dev \
    libtinfo5 \
    libudev-dev \
    libxt-dev \
    net-tools \
    pkg-config \
    sudo \
    unzip \
    wget

RUN curl -sL https://deb.nodesource.com/setup_12.x | bash -

RUN apt-get install -yq nodejs

RUN apt-get clean && rm -rf /var/lib/apt/lists/


RUN mkdir -p /tmp/sc && \
    cd /tmp/sc && \
    wget -q https://github.com/supercollider/supercollider/releases/download/Version-$SC_VERSION/SuperCollider-$SC_VERSION-Source-linux.tar.bz2 -O sc.tar.bz2 && \
    tar xvf sc.tar.bz2

RUN cd /tmp/sc/SuperCollider-Source && \
    mkdir -p build && \
    cd build && \
    cmake -DCMAKE_BUILD_TYPE="Release" \
    -DBUILD_TESTING=OFF \
    -DSUPERNOVA=ON \
    -DNATIVE=OFF \
    -DSC_WII=OFF \
    -DSC_QT=OFF \
    -DSC_ED=OFF \
    -DSC_EL=OFF \
    -DSC_VIM=OFF \
    .. && \
    make -j && \
    make install

RUN mkdir -p /tmp/scp && \
    cd /tmp/scp && \
    wget -q https://github.com/supercollider/sc3-plugins/releases/download/Version-$SCP_VERSION/sc3-plugins-$SCP_VERSION-Source.tar.bz2 -O scp.tar.bz2 && \
    tar xvf scp.tar.bz2

RUN cd /tmp/scp/sc3-plugins-$SCP_VERSION-Source && \
    mkdir -p build && \
    cd build && \
    cmake -DCMAKE_PREFIX_PATH=/usr/lib/x86_64-linux-gnu/ \
    -DCMAKE_INSTALL_PREFIX=/usr/local \
    -DSC_PATH=/tmp/sc/SuperCollider-Source/ \
    -DQUARKS=ON \
    -DNATIVE=OFF \
    -DSUPERNOVA=ON .. && \
    make -j && \
    make install && \
    ldconfig && \
    mkdir /usr/local/share/SuperCollider/Extensions && \
    mv /usr/local/share/SuperCollider/SC3plugins /usr/local/share/SuperCollider/Extensions/SC3plugins


USER tidal
RUN mkdir -p /home/tidal/.local/share/SuperCollider/Extensions
RUN cd /home/tidal/.local/share/SuperCollider/Extensions && git clone https://github.com/musikinformatik/SuperDirt.git SuperDirt && cd SuperDirt && git checkout tags/v1.1.2
RUN cd /home/tidal/.local/share/SuperCollider/Extensions && git clone https://github.com/tidalcycles/Dirt-Samples.git Dirt-Samples
RUN cd /home/tidal/.local/share/SuperCollider/Extensions && git clone https://github.com/supercollider-quarks/Vowel.git Vowel

WORKDIR /home/tidal

# CMD ["bash", "-l", "-c", "./startup.sh"]

ENV SC_JACK_DEFAULT_OUTPUTS=in_jackaudiosrc0_1

CMD ["sclang"]