FROM ubuntu:rolling

LABEL version="1.0"
LABEL description="Docker image for the python interpreter backend."
LABEL name="python-interpreter"

# Set the working directory
WORKDIR /codeapi

COPY core-packages.txt ./
RUN apt update && apt upgrade -y && xargs apt-get -y install < core-packages.txt

COPY apt-packages.txt ./
COPY python.txt ./
RUN xargs apt-get -y install < apt-packages.txt
RUN pip install --no-cache-dir -r python.txt --break-system-packages

WORKDIR /
VOLUME ["/runtime", "/scripts"]
WORKDIR /runtime