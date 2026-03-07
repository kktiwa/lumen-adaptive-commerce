# Iteration 3: Deployment & Production Checklist

## Pre-Launch Checklist

### Environment Setup
- [ ] Python 3.10+ installed
- [ ] Poetry installed
- [ ] OpenAI API key in `.env` file
- [ ] `.env` file in project root with:
  ```
  OPENAI_API_KEY=sk-...
  TAVILY_API_KEY=...
  ARIZE_API_KEY=... (optional)
  ARIZE_SPACE_ID=... (optional)
  ```

### Dependencies
- [ ] Run `poetry install`
- [ ] All dependencies resolved
- [ ] No version conflicts
- [ ] Virtual environment activated

### Code Quality
- [ ] No import errors
- [ ] Type hints on all functions
- [ ] Docstrings on all public functions
- [ ] Error handling in place

## Deployment Stages

### Stage 1: Development (Local)

```bash
poetry run iteration3
```

**What works:**
- ✓ Agent reasoning with LLM
- ✓ Product search and recommendations
- ✓ Order creation
- ✓ Mock payment processing
- ✓ Email service logging
- ✓ Gradio UI

**Limitations:**
- Mock payment processor (not real money)
- In-memory user/product data
- No authentication
- Single user at a time

**Testing:**
- Run sample conversation
- Verify order creation
- Check order totals
- Test payment flow

### Stage 2: Testing & QA

```bash
# Unit tests (if added)
pytest tests/unit/

# Integration tests (if added)
pytest tests/integration/

# Manual testing checklist
```

**Test Scenarios:**

1. **Happy Path**
   - [ ] Start conversation
   - [ ] Provide all info upfront
   - [ ] Get recommendation
   - [ ] Complete purchase
   - [ ] Receive confirmation

2. **Alternative Paths**
   - [ ] Use alternate shipping address
   - [ ] Use alternate payment method
   - [ ] Request product comparison
   - [ ] Cancel mid-purchase

3. **Edge Cases**
   - [ ] Empty message
   - [ ] Vague/unclear input
   - [ ] Payment failure
   - [ ] Network error (simulate)

4. **Error Scenarios**
   - [ ] User not found
   - [ ] Product out of stock
   - [ ] Invalid payment method
   - [ ] Email send failure

### Stage 3: Staging Environment

Before production, set up staging with:

```
┌─────────────────────────────────────────┐
│         Staging Environment             │
├─────────────────────────────────────────┤
│  - PostgreSQL (test database)           │
│  - Stripe test API key                  │
│  - SendGrid test account                │
│  - Real user accounts (testing users)   │
│  - Monitoring & logging                 │
└─────────────────────────────────────────┘
```

**Configuration in `staging.env`:**
```
ENVIRONMENT=staging
DATABASE_URL=postgresql://...
STRIPE_API_KEY=sk_test_...
SENDGRID_API_KEY=...
OPENAI_API_KEY=...
LOG_LEVEL=INFO
```

**Deployment:**
```bash
# Using Docker
docker build -t adaptive-commerce:staging .
docker run -p 7860:7860 --env-file staging.env adaptive-commerce:staging

# Using Docker Compose
docker-compose -f docker-compose.staging.yml up
```

### Stage 4: Production Environment

**Architecture:**
```
                    ┌──────────────────┐
                    │  CloudFlare CDN  │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  API Gateway     │
                    │  (rate limiting) │
                    └────────┬─────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
    ┌───▼────┐          ┌───▼────┐          ┌───▼────┐
    │ Worker │          │ Worker │          │ Worker │
    │   1    │          │   2    │          │   3    │
    └───┬────┘          └───┬────┘          └───┬────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
    ┌───▼──────┐      ┌──────▼──────┐     ┌──────▼──────┐
    │  OpenAI  │      │ PostgreSQL  │     │   Stripe    │
    │   API    │      │  Database   │     │   Payments  │
    └──────────┘      └─────────────┘     └─────────────┘
```

**Production Configuration (`production.env`):**
```
ENVIRONMENT=production
DATABASE_URL=postgresql://prod-user:pass@prod-db:5432/commerce
STRIPE_API_KEY=sk_live_...
SENDGRID_API_KEY=...
OPENAI_API_KEY=...
LOG_LEVEL=WARNING
DEBUG=false
WORKERS=4
PORT=7860
```

### Stage 5: Migration from Mock to Real Services

**Step 1: Database Migration**

```python
# Before: In-memory UserManager
from iteration3.user_management import InMemoryUserManager
user_manager = InMemoryUserManager()

# After: PostgreSQL UserManager
from iteration3.user_management import PostgreSQLUserManager
user_manager = PostgreSQLUserManager(DATABASE_URL)
```

**Step 2: Payment Gateway Integration**

```python
# Before: Mock in payment_processor.py
class PaymentProcessor:
    def process_payment(self, order):
        # Mock implementation
        
# After: Real payment processor
from stripe_payment_processor import StripePaymentProcessor
payment_processor = StripePaymentProcessor(STRIPE_API_KEY)
```

**Step 3: Email Service**

```python
# Before: Mock EmailService
from iteration3.email_service import MockEmailService

# After: Real SendGrid
from sendgrid_email_service import SendGridEmailService
email_service = SendGridEmailService(SENDGRID_API_KEY)
```

**Step 4: Authentication**

```python
# Add user authentication
from auth_service import OAuth2Service
auth_service = OAuth2Service(AUTH0_DOMAIN, AUTH0_CLIENT_ID)

# In agentic_workflow.py:
@tool
def get_current_user():
    """Get authenticated user from request context"""
    return get_request_user()
```

## Monitoring & Observability

### Metrics to Track

```python
# Application metrics
metrics = {
    "conversations_started": 0,
    "products_recommended": 0,
    "orders_completed": 0,
    "payments_successful": 0,
    "payments_failed": 0,
    "emails_sent": 0,
    "avg_conversation_length": 0,
    "avg_time_to_purchase": 0,
}
```

### Logging Configuration

```python
import logging

# Production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler(),
    ]
)

# Sensitive data redaction
logger = logging.getLogger(__name__)
logger.info(f"Processing payment for order: {order_id}")  # OK
# logger.info(f"Payment method: {payment_method}")  # BAD - never log
```

### Alerting Setup

```python
# Alert on critical issues
if payment_success_rate < 0.80:
    send_alert("Payment success rate dropped below 80%")
    
if error_rate > 0.05:  # 5% error rate
    send_alert(f"Error rate: {error_rate}")
    
if avg_response_time > 5000:  # 5 seconds
    send_alert(f"Response time high: {avg_response_time}ms")
```

## Security Hardening

### Before Production Launch

- [ ] Remove hardcoded credentials (use .env)
- [ ] Add input validation on all user inputs
- [ ] Add rate limiting (IP-based, user-based)
- [ ] Enable HTTPS/TLS
- [ ] Add CSRF protection
- [ ] Implement authentication
- [ ] Add authorization (role-based)
- [ ] Sanitize database queries (use ORM)
- [ ] Hash/encrypt sensitive data
- [ ] Audit log all transactions
- [ ] Set up secrets management
- [ ] Regular security updates
- [ ] Vulnerability scanning
- [ ] Penetration testing

### Secrets Management

```python
from pathlib import Path
import os
from dotenv import load_dotenv

# Load from .env in development
load_dotenv()

# Load from AWS Secrets Manager in production
if os.getenv("ENVIRONMENT") == "production":
    import boto3
    client = boto3.client('secretsmanager')
    secret = client.get_secret_value(SecretId='adaptive-commerce/prod')
    # use secret
```

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/chat")
@limiter.limit("30/minute")  # 30 requests per minute per IP
def chat(message: str):
    return process_message(message)
```

## Performance Optimization

### Before Production

- [ ] Add caching (Redis)
- [ ] Database query optimization
- [ ] LLM response caching
- [ ] Image/asset optimization
- [ ] CDN for static files
- [ ] Database connection pooling
- [ ] Load testing

### Load Testing

```bash
# Using locust
pip install locust

# Create locustfile.py and run
locust -f locustfile.py --host=http://localhost:7860

# Simulate 100 users
# Ramp-up: 10 users per second
# Measure: Response times, errors, throughput
```

## Disaster Recovery

### Backup Strategy

```bash
# Daily database backups
pg_dump $DATABASE_URL > backups/db-$(date +%Y%m%d).sql

# Store in S3
aws s3 cp backups/db-*.sql s3://adaptive-commerce-backups/

# Test restore regularly
pg_restore backups/db-20240101.sql
```

### Rollback Plan

```bash
# Version control for deployment
git tag v1.0.0-prod
git tag v1.0.1-prod

# Quick rollback
git checkout v1.0.0-prod
docker build -t adaptive-commerce:v1.0.0 .
docker run ... adaptive-commerce:v1.0.0
```

### High Availability

```yaml
# kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: adaptive-commerce
spec:
  replicas: 3  # 3 instances for HA
  template:
    spec:
      containers:
      - name: app
        image: adaptive-commerce:v1.0.0
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 7860
          initialDelaySeconds: 30
```

## Launch Checklist

### 48 Hours Before Launch

- [ ] All code reviewed and merged
- [ ] Tests passing (100% critical paths)
- [ ] Documentation complete
- [ ] Performance test results acceptable
- [ ] Security audit completed
- [ ] Backup system tested
- [ ] Monitoring alerts configured
- [ ] Team trained on runbooks

### 24 Hours Before Launch

- [ ] Final staging test run-through
- [ ] Database migrations tested
- [ ] Rollback procedure tested
- [ ] Customer support briefed
- [ ] Communication prepared

### Go-Live

- [ ] Monitor every 5 minutes for first hour
- [ ] Monitor every 15 minutes for first 4 hours
- [ ] Monitor every hour for first 24 hours
- [ ] Be ready to rollback
- [ ] Have team on-call

### Post-Launch

- [ ] Monitor metrics daily for 1 week
- [ ] Gather user feedback
- [ ] Track error rates and latency
- [ ] Monitor resource usage
- [ ] Plan improvements for v1.1

## Maintenance Plan

### Weekly
- [ ] Review error logs
- [ ] Monitor resource usage
- [ ] Check backup integrity

### Monthly
- [ ] Security patches
- [ ] Performance tuning
- [ ] User feedback analysis
- [ ] Cost analysis

### Quarterly
- [ ] Penetration testing
- [ ] Disaster recovery drill
- [ ] Capacity planning
- [ ] Architecture review

## Success Metrics

### Technical KPIs
- Response time: < 2 seconds
- Error rate: < 0.1%
- Availability: > 99.5%
- Payment success: > 95%

### Business KPIs
- Conversation completion: > 30%
- Purchase completion: > 15%
- Average order value: > $40
- Customer satisfaction: > 4.0/5.0

## What's Next

After launch, prioritize:

1. **Quick Wins** (1-2 weeks)
   - Bug fixes from user feedback
   - Performance improvements
   - UX refinements

2. **Medium Term** (1-3 months)
   - Multi-item cart
   - User accounts
   - Search improvements
   - Recommendation engine

3. **Long Term** (3-6 months)
   - Mobile app
   - Analytics dashboard
   - Admin portal
   - International expansion

## Questions?

See also:
- [README.md](README.md) - Overview
- [ARCHITECTURE.md](ARCHITECTURE.md) - Design details
- [GETTING_STARTED.md](GETTING_STARTED.md) - Quick start

## Support Contact

For deployment issues:
1. Check logs: `tail -f logs/app.log`
2. Review [ARCHITECTURE.md](ARCHITECTURE.md)
3. Check [GETTING_STARTED.md](GETTING_STARTED.md) troubleshooting
4. Contact team lead

---

**You're ready to launch! Good luck! 🚀**
