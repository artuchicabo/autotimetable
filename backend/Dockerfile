# ===========================
# 1) Base Image
# ===========================
FROM python:3.10-slim

# ===========================
# 2) Set working directory
# ===========================
WORKDIR /app

# ===========================
# 3) Install system dependencies
# ===========================
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ===========================
# 4) Install Python dependencies
# ===========================
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ===========================
# 5) Copy source code
# ===========================
COPY . .

# ===========================
# 6) Create dataset directory if not exists
# ===========================
RUN mkdir -p dataset

# ===========================
# 7) Expose Port
# ===========================
EXPOSE 5000

# ===========================
# 8) Run server
# ===========================
CMD ["python", "app.py"]
