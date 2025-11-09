# Use an official Python runtime as a parent image
FROM python:3.11-slim-buster

# Set the working directory in the container
WORKDIR /usr/src/app

# Define variables
ENV TZ=UTC 
ENV XUMO_PORT 7779
ENV OUTPUT_DIR "playlists"
# Set Python to run in unbuffered mode for real-time logging output
ENV PYTHONUNBUFFERED 1

# Copy requirements and scripts
COPY requirements.txt ./
COPY generate_xumo.py ./
COPY server.py ./

# Install dependencies
# Using --no-cache-dir is already good practice.
RUN pip install --no-cache-dir -r requirements.txt

# Create the output directory as the server expects it
RUN mkdir -p ${OUTPUT_DIR}

# Expose the default port (for documentation)
EXPOSE ${XUMO_PORT}

# Command to run the Flask WSGI server using unbuffered output
# This runs the server.py file, which handles both the web server and the scheduler thread.
CMD [ "python3", "-u", "./server.py" ]
