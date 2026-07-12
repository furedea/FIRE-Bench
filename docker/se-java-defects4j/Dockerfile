FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DEFECTS4J_HOME=/opt/defects4j
ENV PATH="${DEFECTS4J_HOME}/framework/bin:${PATH}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ant \
        build-essential \
        ca-certificates \
        cpanminus \
        curl \
        diffutils \
        git \
        maven \
        openjdk-11-jdk \
        patch \
        perl \
        python3 \
        python3-pip \
        python3-venv \
        subversion \
        unzip \
        wget \
        zip \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 https://github.com/rjust/defects4j.git "${DEFECTS4J_HOME}" \
    && cd "${DEFECTS4J_HOME}" \
    && cpanm --installdeps . \
    && ./init.sh
