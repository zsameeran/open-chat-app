# Use an official Python runtime as the base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the app code and dependencies
COPY . /app/

# Install dependencies
RUN pip install -r requirements.txt

# Expose port 8080
EXPOSE 8080

# Run the app with Gunicorn for production
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
