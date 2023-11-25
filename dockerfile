FROM public.ecr.aws/lambda/python:3.11

# Install system packages, including build essentials
RUN yum update -y && \
    yum install -y \
    gzip \
    tar \
    libreoffice \
    curl \
    wget \
    gcc \
    make \
    libc-dev \
    libffi-dev \
    libxslt-dev \
    zlib1g-dev \
     

# Create a directory for Miniconda
RUN mkdir -p ~/miniconda3

# Download and install Miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh && \
    bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3 && \
    rm -rf ~/miniconda3/miniconda.sh

# Add Miniconda to PATH
ENV PATH="/root/miniconda3/bin:$PATH"

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Run conda init for bash
RUN ~/miniconda3/bin/conda init bash

# Upgrade pip
RUN ~/miniconda3/bin/pip install --upgrade pip

# Install the specified Python packages
RUN pip install -r requirements.txt

# Copy function code
COPY lambda_function.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD [ "lambda_function.handler" ]

#docker build --platform linux/amd64 -t docker-image:test .
#docker run -v  C:\Users\John\Desktop\DockerMount:/mountedvolume -p 8080:8080 docker-image:test .

#pip install --upgrade python-docx
#pip install PyMuPDF
