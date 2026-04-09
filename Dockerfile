# Use a Python 3.12 slim image for an efficient build
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

# Set the working directory in the container
WORKDIR /code

# Install system dependencies (needed for docling and other packages)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file first to leverage Docker cache
COPY app/backend/requirements.txt /code/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /code

# Ensure the start.sh script is executable
RUN chmod +x app/backend/start.sh

# Expose the default Hugging Face Space port
EXPOSE 7860

# Command to run the backend application
# Hugging Face provides PORT environment variable, which start.sh already handles
CMD ["bash", "app/backend/start.sh"]
