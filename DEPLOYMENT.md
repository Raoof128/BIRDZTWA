# 🚀 Deployment Guide

Comprehensive deployment instructions for Browser Isolation System across various platforms and environments.

---

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Cloud Platforms](#cloud-platforms)
  - [AWS](#aws-deployment)
  - [Azure](#azure-deployment)
  - [Google Cloud](#google-cloud-deployment)
- [Bare Metal / VM](#bare-metal--vm-deployment)
- [Production Configuration](#production-configuration)
- [Monitoring & Observability](#monitoring--observability)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Minimum Requirements

- **CPU:** 2 cores
- **RAM:** 4GB (8GB recommended for production)
- **Disk:** 10GB available space
- **OS:** Linux (Ubuntu 20.04+, CentOS 8+, RHEL 8+), macOS, Windows with WSL2

### Software Dependencies

- Docker 20.10+ and Docker Compose 2.0+
- Python 3.10+ (for non-Docker deployments)
- Playwright browsers

---

## 🐳 Docker Deployment

### Quick Start (Recommended)

```bash
# Clone repository
git clone https://github.com/yourusername/browser_isolation.git
cd browser_isolation

# Start services
docker-compose up -d

# Verify deployment
docker-compose ps
curl http://localhost:8000/api/v1/health

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Docker Deployment

```bash
# Build production images
docker-compose -f docker-compose.yml build --no-cache

# Start with production settings
docker-compose up -d

# Scale API instances
docker-compose up -d --scale api=3

# Enable auto-restart
docker-compose up -d --restart unless-stopped
```

### Custom Configuration

```yaml
# docker-compose.override.yml
version: '3.8'

services:
  api:
    environment:
      - LOG_LEVEL=INFO
      - MAX_WORKERS=4
      - TIMEOUT=60
    ports:
      - "8000:8000"
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G

  dashboard:
    environment:
      - STREAMLIT_SERVER_PORT=8501
      - STREAMLIT_SERVER_HEADLESS=true
    ports:
      - "8501:8501"
```

---

## ☸️ Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.20+)
- kubectl configured
- Helm 3.0+ (optional)

### Deployment Files

Create `k8s/deployment.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: browser-isolation

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: browser-isolation-api
  namespace: browser-isolation
spec:
  replicas: 3
  selector:
    matchLabels:
      app: browser-isolation-api
  template:
    metadata:
      labels:
        app: browser-isolation-api
    spec:
      containers:
      - name: api
        image: browser-isolation:1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: LOG_LEVEL
          value: "INFO"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: browser-isolation-api
  namespace: browser-isolation
spec:
  selector:
    app: browser-isolation-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: browser-isolation-api-hpa
  namespace: browser-isolation
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: browser-isolation-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Deploy to Kubernetes

```bash
# Build and push image
docker build -t your-registry/browser-isolation:1.0.0 .
docker push your-registry/browser-isolation:1.0.0

# Deploy
kubectl apply -f k8s/deployment.yaml

# Verify
kubectl get pods -n browser-isolation
kubectl get svc -n browser-isolation

# Get external IP
kubectl get svc browser-isolation-api -n browser-isolation
```

---

## ☁️ Cloud Platforms

### AWS Deployment

#### Option 1: ECS Fargate

```bash
# Install AWS CLI and ECS CLI
pip install awscli
ecs-cli configure

# Create ECS cluster
ecs-cli up --cluster browser-isolation --region us-east-1

# Deploy with Docker Compose
ecs-cli compose --project-name browser-isolation \
  --file docker-compose.yml \
  --cluster browser-isolation \
  service up

# Get service URL
aws ecs list-services --cluster browser-isolation
```

#### Option 2: EC2 with Docker

```bash
# Launch EC2 instance (t3.medium or larger)
# Install Docker
sudo yum update -y
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Deploy
git clone https://github.com/yourusername/browser_isolation.git
cd browser_isolation
docker-compose up -d

# Configure security group
# Allow ports: 22 (SSH), 8000 (API), 8501 (Dashboard)
```

### Azure Deployment

#### Azure Container Instances

```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login
az login

# Create resource group
az group create --name browser-isolation-rg --location eastus

# Create container registry
az acr create --resource-group browser-isolation-rg \
  --name browserisolationreg --sku Basic

# Build and push image
az acr build --registry browserisolationreg \
  --image browser-isolation:1.0.0 .

# Deploy to ACI
az container create --resource-group browser-isolation-rg \
  --name browser-isolation-api \
  --image browserisolationreg.azurecr.io/browser-isolation:1.0.0 \
  --cpu 2 --memory 4 \
  --ports 8000 \
  --ip-address Public \
  --environment-variables LOG_LEVEL=INFO
```

### Google Cloud Deployment

#### Cloud Run

```bash
# Install gcloud CLI
# Login
gcloud auth login

# Set project
gcloud config set project your-project-id

# Build and deploy
gcloud builds submit --tag gcr.io/your-project-id/browser-isolation

gcloud run deploy browser-isolation \
  --image gcr.io/your-project-id/browser-isolation \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --port 8000

# Get URL
gcloud run services describe browser-isolation --region us-central1
```

---

## 🖥️ Bare Metal / VM Deployment

### System Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.10+
sudo apt install python3.10 python3.10-venv python3-pip -y

# Install system dependencies
sudo apt install -y \
  libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
  libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
  libxdamage1 libxfixes3 libxrandr2 libgbm1 \
  libpango-1.0-0 libcairo2 libasound2

# Create application user
sudo useradd -m -s /bin/bash isolation
sudo su - isolation
```

### Application Installation

```bash
# Clone repository
git clone https://github.com/yourusername/browser_isolation.git
cd browser_isolation

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Configure environment
cp .env.example .env
nano .env  # Edit configuration

# Test installation
pytest tests/ -v
```

### Systemd Service

Create `/etc/systemd/system/browser-isolation-api.service`:

```ini
[Unit]
Description=Browser Isolation API Service
After=network.target

[Service]
Type=simple
User=isolation
WorkingDirectory=/home/isolation/browser_isolation
Environment="PATH=/home/isolation/browser_isolation/venv/bin"
ExecStart=/home/isolation/browser_isolation/venv/bin/python api/server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable browser-isolation-api
sudo systemctl start browser-isolation-api
sudo systemctl status browser-isolation-api
```

---

## 🔧 Production Configuration

### Environment Variables

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Security
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com

# Database (if added)
DATABASE_URL=postgresql://user:pass@localhost/isolation

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/browser-isolation/isolation.log

# Performance
MAX_CONCURRENT_RENDERS=50
RENDER_TIMEOUT=60
PAGE_SIZE_LIMIT=52428800

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
```

### Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/browser-isolation
upstream api_backend {
    least_conn;
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;  # If scaled
    server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name api.yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;

    location / {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

---

## 📊 Monitoring & Observability

### Prometheus Metrics

Add to `api/server.py`:

```python
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
render_requests = Counter('isolation_render_requests_total', 'Total render requests')
render_duration = Histogram('isolation_render_duration_seconds', 'Render duration')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Grafana Dashboard

Import dashboard JSON with key metrics:
- Request rate
- Error rate
- Render duration (p50, p95, p99)
- Active renders
- Memory usage
- CPU usage

### Health Checks

```bash
# API health
curl http://localhost:8000/api/v1/health

# Dashboard health
curl http://localhost:8501/_stcore/health

# Docker health
docker ps --format "table {{.Names}}\t{{.Status}}"
```

---

## 🔧 Troubleshooting

### Common Issues

#### Playwright Installation Fails

```bash
# Install system dependencies
sudo apt-get install -y \
  libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
  libcups2 libdrm2 libxkbcommon0 libxcomposite1

# Reinstall Playwright
playwright install --with-deps chromium
```

#### Port Already in Use

```bash
# Find process using port
sudo lsof -i :8000
sudo netstat -tulpn | grep :8000

# Kill process
sudo kill -9 <PID>
```

#### Docker Out of Memory

```bash
# Increase Docker memory limit
# Edit docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G

# Or use Docker Desktop settings (Mac/Windows)
```

#### Permission Errors

```bash
# Fix file permissions
sudo chown -R $(whoami):$(whoami) .

# Fix log directory
sudo mkdir -p /var/log/browser-isolation
sudo chown isolation:isolation /var/log/browser-isolation
```

---

## 📚 Additional Resources

- [QUICKSTART.md](QUICKSTART.md) - Quick setup guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical architecture
- [SECURITY.md](SECURITY.md) - Security best practices
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development guide

---

**Need help? Open an issue or consult the documentation!** 🚀

