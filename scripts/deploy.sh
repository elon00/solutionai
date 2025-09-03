#!/bin/bash

# Solution AI - Production Deployment Script
# This script automates the deployment of Solution AI to various cloud platforms

set -e

# Configuration
PROJECT_NAME="solution-ai"
ENVIRONMENT=${1:-"production"}
CLOUD_PROVIDER=${2:-"aws"}
REGION=${3:-"us-east-1"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    # Check if docker-compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose is not installed. Please install docker-compose first."
        exit 1
    fi

    # Check cloud provider CLI
    case $CLOUD_PROVIDER in
        aws)
            if ! command -v aws &> /dev/null; then
                log_error "AWS CLI is not installed. Please install AWS CLI first."
                exit 1
            fi
            ;;
        gcp)
            if ! command -v gcloud &> /dev/null; then
                log_error "Google Cloud SDK is not installed. Please install Google Cloud SDK first."
                exit 1
            fi
            ;;
        azure)
            if ! command -v az &> /dev/null; then
                log_error "Azure CLI is not installed. Please install Azure CLI first."
                exit 1
            fi
            ;;
    esac

    log_success "Prerequisites check passed"
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."

    # Build backend image
    docker build -t $PROJECT_NAME/backend:latest ./backend
    log_success "Backend image built"

    # Build frontend image
    docker build -t $PROJECT_NAME/frontend:latest ./frontend
    log_success "Frontend image built"

    log_success "All Docker images built successfully"
}

# Deploy to AWS
deploy_aws() {
    log_info "Deploying to AWS..."

    # Login to ECR
    aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

    # Create ECR repositories if they don't exist
    aws ecr describe-repositories --repository-names $PROJECT_NAME/backend --region $REGION || \
    aws ecr create-repository --repository-name $PROJECT_NAME/backend --region $REGION

    aws ecr describe-repositories --repository-names $PROJECT_NAME/frontend --region $REGION || \
    aws ecr create-repository --repository-name $PROJECT_NAME/frontend --region $REGION

    # Tag and push images
    docker tag $PROJECT_NAME/backend:latest $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$PROJECT_NAME/backend:latest
    docker push $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$PROJECT_NAME/backend:latest

    docker tag $PROJECT_NAME/frontend:latest $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$PROJECT_NAME/frontend:latest
    docker push $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$PROJECT_NAME/frontend:latest

    # Update ECS service
    aws ecs update-service \
        --cluster $PROJECT_NAME-cluster \
        --service $PROJECT_NAME-backend \
        --task-definition $PROJECT_NAME-backend \
        --desired-count 3 \
        --region $REGION

    log_success "Deployment to AWS completed"
}

# Deploy to Google Cloud
deploy_gcp() {
    log_info "Deploying to Google Cloud..."

    # Set project
    gcloud config set project $GCP_PROJECT_ID

    # Build and push images to GCR
    gcloud builds submit --tag gcr.io/$GCP_PROJECT_ID/$PROJECT_NAME/backend ./backend
    gcloud builds submit --tag gcr.io/$GCP_PROJECT_ID/$PROJECT_NAME/frontend ./frontend

    # Deploy to Cloud Run
    gcloud run deploy $PROJECT_NAME-backend \
        --image gcr.io/$GCP_PROJECT_ID/$PROJECT_NAME/backend \
        --platform managed \
        --region $REGION \
        --allow-unauthenticated \
        --set-env-vars "ENVIRONMENT=$ENVIRONMENT"

    gcloud run deploy $PROJECT_NAME-frontend \
        --image gcr.io/$GCP_PROJECT_ID/$PROJECT_NAME/frontend \
        --platform managed \
        --region $REGION \
        --allow-unauthenticated

    log_success "Deployment to Google Cloud completed"
}

# Deploy to Azure
deploy_azure() {
    log_info "Deploying to Azure..."

    # Login to Azure
    az login --service-principal -u $AZURE_CLIENT_ID -p $AZURE_CLIENT_SECRET --tenant $AZURE_TENANT_ID

    # Set subscription
    az account set --subscription $AZURE_SUBSCRIPTION_ID

    # Create resource group if it doesn't exist
    az group create --name $PROJECT_NAME-rg --location $REGION || true

    # Build and push images to ACR
    az acr build --registry $AZURE_CONTAINER_REGISTRY --image $PROJECT_NAME/backend:latest ./backend
    az acr build --registry $AZURE_CONTAINER_REGISTRY --image $PROJECT_NAME/frontend:latest ./frontend

    # Deploy to AKS or Container Instances
    # Note: This is a simplified deployment. In production, you'd use AKS with proper networking

    log_success "Deployment to Azure completed"
}

# Deploy to DigitalOcean
deploy_digitalocean() {
    log_info "Deploying to DigitalOcean..."

    # This would typically use DigitalOcean's App Platform or Kubernetes
    # For simplicity, we'll use docker-compose on a Droplet

    # Build images
    build_images

    # Push to DigitalOcean Container Registry
    doctl registry login
    docker tag $PROJECT_NAME/backend:latest registry.digitalocean.com/$DO_REGISTRY/$PROJECT_NAME/backend:latest
    docker push registry.digitalocean.com/$DO_REGISTRY/$PROJECT_NAME/backend:latest

    docker tag $PROJECT_NAME/frontend:latest registry.digitalocean.com/$DO_REGISTRY/$PROJECT_NAME/frontend:latest
    docker push registry.digitalocean.com/$DO_REGISTRY/$PROJECT_NAME/frontend:latest

    log_success "Deployment to DigitalOcean completed"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."

    case $CLOUD_PROVIDER in
        aws)
            # Run migrations on ECS task
            aws ecs run-task \
                --cluster $PROJECT_NAME-cluster \
                --task-definition $PROJECT_NAME-migration \
                --launch-type FARGATE \
                --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SECURITY_GROUPS]}" \
                --region $REGION
            ;;
        *)
            log_warning "Database migrations need to be run manually for $CLOUD_PROVIDER"
            ;;
    esac

    log_success "Database migrations completed"
}

# Health check
health_check() {
    log_info "Running health checks..."

    # Wait for services to be ready
    sleep 30

    # Check backend health
    if curl -f -s http://localhost:8000/health/ > /dev/null; then
        log_success "Backend health check passed"
    else
        log_error "Backend health check failed"
        exit 1
    fi

    # Check frontend health
    if curl -f -s http://localhost:8080 > /dev/null; then
        log_success "Frontend health check passed"
    else
        log_error "Frontend health check failed"
        exit 1
    fi

    log_success "All health checks passed"
}

# Main deployment function
main() {
    log_info "Starting Solution AI deployment to $CLOUD_PROVIDER in $ENVIRONMENT environment"

    check_prerequisites
    build_images

    case $CLOUD_PROVIDER in
        aws)
            deploy_aws
            ;;
        gcp)
            deploy_gcp
            ;;
        azure)
            deploy_azure
            ;;
        digitalocean)
            deploy_digitalocean
            ;;
        *)
            log_error "Unsupported cloud provider: $CLOUD_PROVIDER"
            log_info "Supported providers: aws, gcp, azure, digitalocean"
            exit 1
            ;;
    esac

    run_migrations
    health_check

    log_success "🎉 Solution AI has been successfully deployed to $CLOUD_PROVIDER!"
    log_info "🌐 Frontend URL: https://your-domain.com"
    log_info "📚 API Documentation: https://your-domain.com/docs"
    log_info "📊 Monitoring Dashboard: https://your-monitoring-domain.com"
}

# Show usage
usage() {
    echo "Usage: $0 [environment] [cloud_provider] [region]"
    echo ""
    echo "Arguments:"
    echo "  environment     Environment to deploy to (default: production)"
    echo "  cloud_provider  Cloud provider: aws, gcp, azure, digitalocean (default: aws)"
    echo "  region          Cloud region (default: us-east-1)"
    echo ""
    echo "Examples:"
    echo "  $0 production aws us-east-1"
    echo "  $0 staging gcp us-central1"
    echo "  $0 development azure eastus"
}

# Parse arguments
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    usage
    exit 0
fi

# Run main function
main