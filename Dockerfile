FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Prevent Python from buffering stdout/stderr (good for logging in containers)
ENV PYTHONUNBUFFERED=1

# Copy requirement manifest and install deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
# Ensure we copy the actual main server file used in this repo
COPY main_server.py ./
COPY README.md ./

# EXPOSE documents the port the container listens on at runtime.
# FastMCP's transport may open different ports depending on configuration;
# the default historically used in this project was 5000/5100 — adjust at runtime if needed.
EXPOSE 5000

# Default RSS feed placeholder. It's recommended to set RSS_FEED_URL at runtime instead
ENV RSS_FEED_URL="https://www.sirishgurung.com/rss.xml"

# Run the main server
CMD ["python", "main_server.py"]

