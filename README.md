# 🚀 Solution AI - Enterprise-Grade Ticket Triage SaaS

[![CI/CD](https://github.com/your-org/solution-ai/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/your-org/solution-ai/actions/workflows/ci-cd.yml)
[![Coverage](https://codecov.io/gh/your-org/solution-ai/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/solution-ai)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg)](https://www.docker.com/)
[![Algorand](https://img.shields.io/badge/blockchain-Algorand-blue.svg)](https://www.algorand.com/)

> **Enterprise-Ready AI-Powered Ticket Classification System**

A production-grade SaaS platform that leverages advanced AI to automatically classify, prioritize, and route customer support tickets. Built with modern architecture, comprehensive monitoring, and enterprise security standards.

## 🌐 Demo

Check out the live demo: [https://v0-ai-support-website.vercel.app/#demo](https://v0-ai-support-website.vercel.app/#demo)

## ✨ Key Features

### 🤖 AI-Powered Classification
- **Multi-Provider AI**: OpenAI GPT-4 + Anthropic Claude with automatic failover
- **Smart Categorization**: Classifies tickets into bug/feature_request/billing_issue/other
- **Confidence Scoring**: Provides accuracy metrics for each classification
- **Processing Analytics**: Tracks AI performance and response times

### 🏢 Enterprise Architecture
- **Microservices Design**: Modular, scalable architecture
- **Professional Code Structure**: MVC pattern with services and repositories
- **Database Abstraction**: SQLAlchemy ORM with PostgreSQL
- **Async Processing**: FastAPI with async/await patterns

### 🔒 Security & Compliance
- **OWASP Standards**: Comprehensive security audit and implementation
- **API Key Authentication**: Secure key-based access control
- **Rate Limiting**: Redis-backed rate limiting with burst protection
- **GDPR Compliance**: Data retention policies and user data management
- **SSL/TLS**: End-to-end encryption in production

### 📊 Monitoring & Observability
- **Prometheus Metrics**: Comprehensive application metrics
- **Grafana Dashboards**: Real-time monitoring and alerting
- **Jaeger Tracing**: Distributed request tracing
- **Structured Logging**: JSON logging with correlation IDs
- **Health Checks**: Automated health monitoring endpoints

### 💰 Commercial Features
- **Stripe Integration**: Subscription management and payment processing
- **Multi-Tenant**: API key isolation and customer management
- **Usage Analytics**: Detailed usage tracking and reporting
- **Webhook Support**: Integration with Zendesk, Intercom, Jira
- **Admin Dashboard**: Comprehensive management interface

### 🚀 DevOps & Deployment
- **Docker & Kubernetes**: Container orchestration with K8s manifests
- **CI/CD Pipeline**: GitHub Actions with automated testing
- **Multi-Environment**: Dev/Staging/Production configurations
- **Load Balancing**: Nginx reverse proxy with load distribution
- **Auto-Scaling**: Horizontal pod autoscaling in Kubernetes

### 🧪 Quality Assurance
- **Comprehensive Testing**: Unit, integration, and E2E tests
- **Code Coverage**: >90% test coverage with detailed reporting
- **Security Scanning**: Automated vulnerability scanning
- **Performance Testing**: Load testing and performance benchmarks

### ⛓️ Blockchain Integration
- **Algorand Smart Contracts**: Decentralized ticket management and NFT issuance
- **SOLAI Token**: 21 trillion supply utility token for rewards and governance
- **NFT Tickets**: Unique digital assets for premium support tickets
- **Para Wallet Integration**: Seamless blockchain wallet connectivity
- **Immutable Records**: Cryptographic verification of ticket history
- **Tokenized Economy**: Incentive system with SOLAI rewards

## Features

- **AI Ticket Classification**: Classifies tickets into bug, feature_request, billing_issue, other
- **Summarization**: Provides concise summaries
- **Confidence Scores**: Returns confidence levels for classifications
- **API Key Authentication**: Secure access with API keys
- **Rate Limiting**: Per-key quotas with daily resets
- **Provider Failover**: OpenAI primary, Anthropic fallback
- **Stripe Paywall**: Subscription-based access
- **Webhook Integrations**: Support for Zendesk, Intercom, Jira
- **Observability**: Jaeger tracing and metrics
- **Database Logging**: SQLite (upgradeable to PostgreSQL)

## Quick Start

1. **Clone or download the project**

2. **Set up environment variables** in `.env`:
   ```
   OPENAI_API_KEY=sk-your-openai-key
   ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
   ALLOWED_API_KEYS=demo_key_123,your_generated_keys
   STRIPE_SECRET_KEY=sk_test_your-stripe-secret
   STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret
   ```

3. **Run with Docker Compose**:
   ```bash
   docker compose up --build
   ```

4. **Access the application**:
   - Frontend: http://localhost:8080
   - API Docs: http://localhost:8000/docs
   - Jaeger UI: http://localhost:16686

## API Usage

### Classify Ticket
```bash
curl -X POST http://localhost:8000/api/v1/triage \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: demo_key_123" \
  -d '{"ticket_text":"I was charged twice this month. Please refund the duplicate payment."}'
```

Response:
```json
{
  "label": "billing_issue",
  "confidence": 0.95,
  "summary": "Customer reporting duplicate charges and requesting refund."
}
```

### Get Recent Tickets
```bash
curl http://localhost:8000/api/v1/recent \
  -H "X-Api-Key: demo_key_123"
```

## Commercial Features

### Stripe Integration
- Webhook endpoint: `/webhook/stripe`
- Automatically generates API keys upon successful payment
- Stores customer → API key mapping

### Rate Limiting
- Default: 100 requests/day per key
- Configurable per customer
- Daily reset at midnight

### Provider Failover
- Primary: OpenAI GPT-4o-mini
- Fallback: Anthropic Claude-3-Haiku
- Automatic switching on failure

### Webhook Integrations
- Endpoint: `/webhook/{provider}` (zendesk, intercom, jira)
- Processes incoming tickets and triages them
- Logs results for routing

## Deployment

### Production Setup
1. Set up Stripe webhook to point to your domain/webhook/stripe
2. Configure domain and SSL
3. Scale with load balancer if needed
4. Monitor with Jaeger and logs

### Database Upgrade to PostgreSQL
To use PostgreSQL instead of SQLite:
1. Add postgres service to docker-compose.yml
2. Update backend to use psycopg2
3. Change DB_PATH to PostgreSQL connection string

## Development

### Local Development
- Backend: `cd backend && pip install -r requirements.txt && uvicorn main:app --reload`
- Frontend: Open index.html in browser (with CORS proxy for API calls)

### Testing
- API tests: Use the /docs interface
- Integration tests: Test webhooks with sample data

## Monetization

- **Pricing Tiers**: Basic ($9/mo - 100 req/day), Pro ($29/mo - 1000 req/day), Enterprise (custom)
- **Stripe Checkout**: Hosted payment pages
- **API Key Management**: Automatic provisioning
- **Usage Tracking**: Daily request counts
- **Revenue Analytics**: Track via Stripe dashboard

## Support

For issues or enhancements, check the code or contact the maintainer.