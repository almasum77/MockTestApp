# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install necessary build tools and dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Rust and Cargo
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Set the working directory in the container
WORKDIR /app

COPY ./requirements.txt /app 

# Upgrade pip and install any needed packages specified in requirements.txt
# RUN pip install --upgrade pip
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

# Download and link spaCy model
RUN python -m spacy download en_core_web_sm

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV NAME World



# Run app.py when the container launches
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80"]
