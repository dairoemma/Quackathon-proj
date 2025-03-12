# Use an official Python runtime as the base image
FROM python:3.12

# Set the working directory
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the FastAPI app files into the container
COPY . .

# Expose the port FastAPI will run on
EXPOSE 8000

# Set environment variables for MongoDB and Redis
ENV MONGO_URI=mongodb://mongo:27017
ENV REDIS_HOST=redis
ENV REDIS_PORT=6379

# Run the FastAPI application
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
