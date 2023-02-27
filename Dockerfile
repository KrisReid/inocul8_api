# Use an official Python runtime as the base image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /api

# Copy the requirements file to the container
COPY main.py ./
COPY requirements.txt ./

# Install required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code to the container
# COPY . .

# Set environment variables
ENV FLASK_APP=main.py
# ENV FLASK_ENV=local
ENV FLASK_ENV=development

# Expose port 5000 for Flask to listen on
EXPOSE 3306

# Run the Flask application
CMD ["flask", "run", "--host=0.0.0.0"]