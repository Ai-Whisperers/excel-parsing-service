# Use Python 3.11 slim image
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app

# Expose ports
# 8000: REST API (control plane)
# 8815: Arrow Flight gRPC (data plane)
EXPOSE 8000 8815

# Run application (starts both REST and Flight servers)
CMD ["python", "-m", "app.main"]
