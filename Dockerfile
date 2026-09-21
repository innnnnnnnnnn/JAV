FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure .env is copied if user hasn't ignored it, 
# or use internal env vars (OCI recommended for secrets)
# For simplicity, we copy everything but user should use .dockerignore

# Command to run the bot
CMD ["python", "-u", "main.py"]
