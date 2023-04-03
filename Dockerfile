# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -

# Copy Poetry files
COPY poetry.lock pyproject.toml /app/

# Install dependencies
RUN /root/.poetry/bin/poetry config virtualenvs.create false && \
    /root/.poetry/bin/poetry install --no-dev --no-interaction --no-ansi

# Expose the port the app runs on
EXPOSE 5000

# Set environment variable
ENV FLASK_APP app.py
ENV PYSPARK_GATEWAY_PORT 4089
ENV PYSPARK_GATEWAY_SECRET ofas
ENV PYSPARK_PIN_THREAD true

# Run app.py when the container launches
CMD ["flask", "run", "--host=0.0.0.0"]