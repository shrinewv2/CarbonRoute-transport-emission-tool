# CarbonRoute AWS Deployment Guide

## Quick Start - AWS App Runner Deployment

### Prerequisites
- AWS Account with appropriate permissions
- GitHub account with your CarbonRoute code
- MongoDB Atlas account (free tier available)

### Step 1: Prepare Application for AWS

#### 1.1 Create Backend Dockerfile
```dockerfile
# /app/Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .
COPY airports.json .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 1.2 Create Frontend Dockerfile
```dockerfile
# /app/frontend/Dockerfile
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html

# Custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### 1.3 Create nginx.conf for frontend
```nginx
server {
    listen 80;
    server_name localhost;
    
    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Step 2: Setup MongoDB Atlas

1. Go to [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Create account and new project
3. Create free M0 cluster
4. Setup database user and IP whitelist
5. Get connection string: `mongodb+srv://username:password@cluster.mongodb.net/carbonroute`

### Step 3: Deploy Backend with AWS App Runner

#### 3.1 Create apprunner.yaml
```yaml
version: 1.0
runtime: docker
build:
  commands:
    build:
      - echo "Building backend..."
run:
  runtime-version: latest
  command: uvicorn server:app --host 0.0.0.0 --port 8000
  network:
    port: 8000
    env: PORT
  env:
    - name: MONGO_URL
      value: "your-mongodb-atlas-connection-string"
    - name: GOOGLE_MAPS_API_KEY  
      value: "your-google-maps-api-key"
    - name: DB_NAME
      value: "carbonroute"
```

#### 3.2 Deploy Steps:
1. **Push code to GitHub**
2. **AWS Console → App Runner**
3. **Create Service:**
   - Source: Repository
   - Connect to GitHub
   - Repository: your-repo/carbonroute
   - Branch: main
   - Build settings: Use apprunner.yaml
4. **Configure Service:**
   - Service name: carbonroute-backend
   - Port: 8000
5. **Environment Variables:**
   - Add all required env vars
6. **Deploy and get URL**

### Step 4: Deploy Frontend to S3 + CloudFront

#### 4.1 Build and Upload Frontend
```bash
# Build frontend
cd frontend
npm run build

# Upload to S3
aws s3 mb s3://your-carbonroute-frontend
aws s3 sync build/ s3://your-carbonroute-frontend --delete
```

#### 4.2 Configure S3 Bucket
```bash
# Enable static website hosting
aws s3 website s3://your-carbonroute-frontend \
  --index-document index.html \
  --error-document index.html
```

#### 4.3 Create CloudFront Distribution
```json
{
  "CallerReference": "carbonroute-frontend",
  "Origins": {
    "Items": [
      {
        "Id": "S3-carbonroute",
        "DomainName": "your-carbonroute-frontend.s3-website-region.amazonaws.com",
        "CustomOriginConfig": {
          "HTTPPort": 80,
          "OriginProtocolPolicy": "http-only"
        }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-carbonroute",
    "ViewerProtocolPolicy": "redirect-to-https",
    "TrustedSigners": {
      "Enabled": false
    }
  },
  "Enabled": true
}
```

### Step 5: Environment Configuration

#### 5.1 Update Frontend Environment
Create `/app/frontend/.env.production`:
```bash
REACT_APP_BACKEND_URL=https://your-app-runner-url.region.awsapprunner.com
```

#### 5.2 Backend Environment Variables in App Runner:
```
MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/carbonroute
GOOGLE_MAPS_API_KEY=your_api_key
DB_NAME=carbonroute
```

## Alternative: Complete ECS Deployment

### Infrastructure as Code with Terraform

#### main.tf
```hcl
provider "aws" {
  region = "us-west-2"
}

# VPC and Networking
resource "aws_vpc" "carbonroute_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "carbonroute-vpc"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "carbonroute_igw" {
  vpc_id = aws_vpc.carbonroute_vpc.id
  
  tags = {
    Name = "carbonroute-igw"
  }
}

# Public Subnets
resource "aws_subnet" "public_subnet_1" {
  vpc_id                  = aws_vpc.carbonroute_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-west-2a"
  map_public_ip_on_launch = true
  
  tags = {
    Name = "carbonroute-public-1"
  }
}

resource "aws_subnet" "public_subnet_2" {
  vpc_id                  = aws_vpc.carbonroute_vpc.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "us-west-2b"
  map_public_ip_on_launch = true
  
  tags = {
    Name = "carbonroute-public-2"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "carbonroute_cluster" {
  name = "carbonroute-cluster"
}

# Application Load Balancer
resource "aws_lb" "carbonroute_alb" {
  name               = "carbonroute-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets           = [aws_subnet.public_subnet_1.id, aws_subnet.public_subnet_2.id]
}
```

### Deployment Commands

#### Using AWS CLI and Docker
```bash
# 1. Build and push images to ECR
aws ecr create-repository --repository-name carbonroute-backend
aws ecr create-repository --repository-name carbonroute-frontend

# Get login token
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin account-id.dkr.ecr.us-west-2.amazonaws.com

# Build and push backend
docker build -t carbonroute-backend .
docker tag carbonroute-backend:latest account-id.dkr.ecr.us-west-2.amazonaws.com/carbonroute-backend:latest
docker push account-id.dkr.ecr.us-west-2.amazonaws.com/carbonroute-backend:latest

# Build and push frontend  
cd frontend
docker build -t carbonroute-frontend .
docker tag carbonroute-frontend:latest account-id.dkr.ecr.us-west-2.amazonaws.com/carbonroute-frontend:latest
docker push account-id.dkr.ecr.us-west-2.amazonaws.com/carbonroute-frontend:latest

# 2. Deploy to ECS
aws ecs create-service \
  --cluster carbonroute-cluster \
  --service-name carbonroute-backend \
  --task-definition carbonroute-backend:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345,subnet-67890],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
```

## Cost Estimation

### App Runner Option (Simplest)
- **App Runner Backend**: ~$25-50/month
- **S3 + CloudFront Frontend**: ~$5-15/month  
- **MongoDB Atlas**: Free (M0) or $9/month (M2)
- **Total**: ~$30-75/month

### ECS Option (Production)
- **ECS Fargate**: ~$30-100/month (depending on usage)
- **Application Load Balancer**: ~$20/month
- **S3 + CloudFront**: ~$5-15/month
- **MongoDB Atlas**: $9-25/month
- **Total**: ~$65-160/month

## Security Best Practices

1. **Environment Variables**: Store in AWS Systems Manager Parameter Store
2. **HTTPS**: Use AWS Certificate Manager for free SSL certificates
3. **IAM**: Create specific roles for each service
4. **VPC**: Use private subnets for backend services
5. **Security Groups**: Restrict access to necessary ports only

## Monitoring and Logging

```bash
# CloudWatch Logs
aws logs create-log-group --log-group-name /aws/ecs/carbonroute

# CloudWatch Alarms
aws cloudwatch put-metric-alarm \
  --alarm-name carbonroute-high-cpu \
  --alarm-description "High CPU utilization" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold
```

## Custom Domain Setup

1. **Register domain** in Route 53 or use existing domain
2. **Request SSL certificate** in AWS Certificate Manager
3. **Configure CloudFront** to use custom domain
4. **Update DNS** to point to CloudFront distribution

## Backup and Disaster Recovery

1. **MongoDB Atlas**: Automatic backups included
2. **Application Code**: GitHub repository
3. **Infrastructure**: Terraform state in S3 backend
4. **Frontend Assets**: S3 versioning enabled

This setup will give you a production-ready, scalable CarbonRoute deployment on AWS!