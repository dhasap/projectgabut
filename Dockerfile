FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (needed for some python packages like cryptography/mysql)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to cache dependencies
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Run the bot
CMD ["python3", "bot.py"]