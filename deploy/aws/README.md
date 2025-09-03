# AWS Deployment Guide for Solution AI

## 🚀 Production Deployment on AWS

This guide provides step-by-step instructions for deploying Solution AI to AWS with enterprise-grade infrastructure.

## 📋 Prerequisites

- AWS CLI configured with appropriate permissions
- Domain name registered
- SSL certificate (can be obtained via AWS Certificate Manager)

## 🏗️ Infrastructure Components

### 1. **VPC and Networking**
```bash
# Create VPC with public and private subnets
aws ec2 create-vpc --cidr-block 10.0.0.0/16
aws ec2 create-subnet --vpc-id vpc-xxxxx --cidr-block 10.0.1.0/24 --availability-zone us-east-1a
aws ec2 create-subnet --vpc-id vpc-xxxxx --cidr-block 10.0.2.0/24 --availability-zone us-east-1b
```

### 2. **ECS Fargate Cluster**
```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name solution-ai-cluster

# Register task definitions
aws ecs register-task-definition --cli-input-json file://aws/task-definition.json
```

### 3. **RDS PostgreSQL Database**
```bash
# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier solution-ai-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --master-username solution_user \
  --master-user-password YOUR_SECURE_PASSWORD \
  --allocated-storage 20 \
  --vpc-security-group-ids sg-xxxxx \
  --db-subnet-group-name solution-ai-db-subnet
```

### 4. **ElastiCache Redis**
```bash
# Create Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id solution-ai-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1
```

### 5. **Application Load Balancer**
```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name solution-ai-alb \
  --subnets subnet-xxxxx subnet-yyyyy \
  --security-groups sg-xxxxx
```

## 🔧 Configuration Files

### Environment Variables for Production
```bash
# .env.production
DATABASE_URL=postgresql://solution_user:password@solution-ai-db.xxxxxx.us-east-1.rds.amazonaws.com:5432/solution_ai
REDIS_URL=redis://solution-ai-redis.xxxxxx.ng.0001.use1.cache.amazonaws.com:6379
OPENAI_API_KEY=sk-your-production-key
STRIPE_SECRET_KEY=sk_live_your-stripe-key
STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret
ALLOWED_API_KEYS=prod_key_1,prod_key_2
LOG_LEVEL=INFO
ENABLE_CACHING=true
ENABLE_METRICS=true
```

## 🚀 Deployment Steps

### 1. **Build and Push Docker Images**
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin xxxxxx.dkr.ecr.us-east-1.amazonaws.com

# Build and push backend
docker build -t solutionai/backend ./backend
docker tag solutionai/backend:latest xxxxxx.dkr.ecr.us-east-1.amazonaws.com/solutionai/backend:latest
docker push xxxxxx.dkr.ecr.us-east-1.amazonaws.com/solutionai/backend:latest

# Build and push frontend
docker build -t solutionai/frontend ./frontend
docker tag solutionai/frontend:latest xxxxxx.dkr.ecr.us-east-1.amazonaws.com/solutionai/frontend:latest
docker push xxxxxx.dkr.ecr.us-east-1.amazonaws.com/solutionai/frontend:latest
```

### 2. **Deploy to ECS**
```bash
# Update service with new task definition
aws ecs update-service \
  --cluster solution-ai-cluster \
  --service solution-ai-backend \
  --task-definition solution-ai-backend:1 \
  --desired-count 3
```

### 3. **Configure CloudFront (Optional)**
```bash
# Create CloudFront distribution for global CDN
aws cloudfront create-distribution --distribution-config file://aws/cloudfront-config.json
```

## 📊 Monitoring Setup

### CloudWatch Alarms
```bash
# Create CPU utilization alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "HighCPUUtilization" \
  --alarm-description "CPU utilization is high" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=ClusterName,Value=solution-ai-cluster Name=ServiceName,Value=solution-ai-backend \
  --evaluation-periods 2
```

### X-Ray Integration
- Enable X-Ray tracing in ECS task definition
- Configure sampling rules for optimal performance
- Set up CloudWatch dashboards for tracing data

## 🔒 Security Configuration

### Security Groups
```bash
# ALB Security Group (allows HTTP/HTTPS)
aws ec2 create-security-group \
  --group-name solution-ai-alb-sg \
  --description "ALB Security Group" \
  --vpc-id vpc-xxxxx

aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0
```

### WAF Configuration
```bash
# Create WAF WebACL
aws wafv2 create-web-acl \
  --name solution-ai-waf \
  --scope REGIONAL \
  --default-action Allow={} \
  --rules file://aws/waf-rules.json
```

## 💰 Cost Optimization

### Auto Scaling
```bash
# Configure auto scaling
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/solution-ai-cluster/solution-ai-backend \
  --min-capacity 2 \
  --max-capacity 10

aws application-autoscaling put-scaling-policy \
  --policy-name cpu-scaling-policy \
  --service-namespace ecs \
  --resource-id service/solution-ai-cluster/solution-ai-backend \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://aws/scaling-policy.json
```

## 📈 Production Checklist

- [ ] VPC and subnets configured
- [ ] Security groups properly configured
- [ ] RDS PostgreSQL instance running
- [ ] ElastiCache Redis cluster active
- [ ] ECS cluster and services created
- [ ] Application Load Balancer configured
- [ ] SSL certificate installed
- [ ] CloudWatch monitoring enabled
- [ ] Backup strategy implemented
- [ ] Auto scaling configured
- [ ] WAF protection enabled
- [ ] Domain DNS configured
- [ ] Health checks passing

## 🚨 Emergency Procedures

### Rolling Back Deployments
```bash
# Rollback to previous task definition
aws ecs update-service \
  --cluster solution-ai-cluster \
  --service solution-ai-backend \
  --task-definition solution-ai-backend:2 \
  --desired-count 3
```

### Database Recovery
```bash
# Restore from backup
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier solution-ai-db-restore \
  --db-snapshot-identifier solution-ai-backup-2024-01-01
```

## 📞 Support

For deployment issues, check:
1. ECS service events
2. CloudWatch logs
3. ALB access logs
4. RDS performance insights
5. X-Ray traces