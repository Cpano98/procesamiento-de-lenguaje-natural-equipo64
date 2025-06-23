# Deposits Transactions Secured Card Service

This service manages secured card transactions, vault balances, and auto-funding functionality for the Stori platform. It provides a RESTful API for handling various operations related to secured cards, including balance management, transaction history, and automated funding.

## Service Overview

The Deposits Transactions Secured Card service is built using Go and follows a clean architecture pattern with clear separation of concerns:

- **Domain Layer**: Contains business models and interfaces
- **Application Layer**: Implements business logic and use cases
- **Infrastructure Layer**: Handles HTTP routing, middleware, and external service integrations
- **Adapters Layer**: Provides implementations for external services and validators

## API Endpoints

The service exposes the following endpoints under the `/v1/deposits-securedcard` base path:

### Health Check
- `GET /health` - Health check endpoint (no middleware applied)

**Curl Example:**
```bash
curl -X GET "https://api.example.com/health"
```

**Response Example:**
```json
{
  "status": "ok",
  "timestamp": "2023-04-01T12:00:00Z"
}
```

### User Movements
- `GET /user/movements` - Retrieves transaction history for a user's secured card
  - Requires user authentication and standard headers

**Curl Example:**
```bash
curl -X GET "https://api.example.com/v1/deposits-securedcard/user/movements" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "User-ID: USER_ID" \
  -H "Content-Type: application/json"
```

**Response Example:**
```json
{
  "movements": [
    {
      "id": "mov_123456789",
      "type": "DEPOSIT",
      "amount": 100.50,
      "currency": "MXN",
      "status": "COMPLETED",
      "created_at": "2023-03-15T10:30:00Z",
      "description": "Deposit to secured card"
    },
    {
      "id": "mov_987654321",
      "type": "WITHDRAWAL",
      "amount": 50.25,
      "currency": "MXN",
      "status": "COMPLETED",
      "created_at": "2023-03-14T15:45:00Z",
      "description": "Withdrawal from secured card"
    }
  ],
  "pagination": {
    "total": 2,
    "page": 1,
    "per_page": 10
  }
}
```

### Vault Balance Management
- `GET /vault/balance` - Retrieves the current vault balance

**Curl Example:**
```bash
curl -X GET "https://api.example.com/v1/deposits-securedcard/vault/balance" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "User-ID: USER_ID" \
  -H "Content-Type: application/json"
```

**Response Example:**
```json
{
  "balance": 1500.75,
  "currency": "MXN",
  "last_updated": "2023-03-15T10:30:00Z"
}
```

- `POST /vault/balance/increase` - Increases the user's vault balance

**Curl Example:**
```bash
curl -X POST "https://api.example.com/v1/deposits-securedcard/vault/balance/increase" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "User-ID: USER_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 200.00,
    "currency": "MXN",
    "description": "Deposit to vault"
  }'
```

**Response Example:**
```json
{
  "transaction_id": "txn_123456789",
  "status": "COMPLETED",
  "amount": 200.00,
  "currency": "MXN",
  "new_balance": 1700.75,
  "created_at": "2023-03-15T11:00:00Z"
}
```

- `POST /vault/balance/decrease` - Decreases the user's vault balance

**Curl Example:**
```bash
curl -X POST "https://api.example.com/v1/deposits-securedcard/vault/balance/decrease" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "User-ID: USER_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 100.00,
    "currency": "MXN",
    "description": "Withdrawal from vault"
  }'
```

**Response Example:**
```json
{
  "transaction_id": "txn_987654321",
  "status": "COMPLETED",
  "amount": 100.00,
  "currency": "MXN",
  "new_balance": 1600.75,
  "created_at": "2023-03-15T11:30:00Z"
}
```

### Auto-Funding
- `POST /balance/increase/auto-fund` - Creates a new auto-funding configuration

**Curl Example:**
```bash
curl -X POST "https://api.example.com/v1/deposits-securedcard/balance/increase/auto-fund" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "User-ID: USER_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 500.00,
    "currency": "MXN",
    "frequency": "WEEKLY",
    "day_of_week": 1,
    "day_of_month": null,
    "source_account": "ACC123456789",
    "enabled": true
  }'
```

**Response Example:**
```json
{
  "auto_fund_id": "af_123456789",
  "status": "ACTIVE",
  "amount": 500.00,
  "currency": "MXN",
  "frequency": "WEEKLY",
  "day_of_week": 1,
  "day_of_month": null,
  "source_account": "ACC123456789",
  "enabled": true,
  "created_at": "2023-03-15T12:00:00Z",
  "next_execution": "2023-03-20T00:00:00Z"
}
```

- `GET /balance/increase/auto-fund` - Retrieves auto-funding details

**Curl Example:**
```bash
curl -X GET "https://api.example.com/v1/deposits-securedcard/balance/increase/auto-fund" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "User-ID: USER_ID" \
  -H "Content-Type: application/json"
```

**Response Example:**
```json
{
  "auto_fund_id": "af_123456789",
  "status": "ACTIVE",
  "amount": 500.00,
  "currency": "MXN",
  "frequency": "WEEKLY",
  "day_of_week": 1,
  "day_of_month": null,
  "source_account": "ACC123456789",
  "enabled": true,
  "created_at": "2023-03-15T12:00:00Z",
  "next_execution": "2023-03-20T00:00:00Z",
  "last_execution": "2023-03-13T00:00:00Z",
  "execution_history": [
    {
      "execution_id": "exec_123456789",
      "status": "COMPLETED",
      "amount": 500.00,
      "executed_at": "2023-03-13T00:00:00Z"
    }
  ]
}
```

- `PATCH /balance/increase/auto-fund` - Updates an existing auto-funding configuration
  - Requires user authentication and mandatory headers

**Curl Example:**
```bash
curl -X PATCH "https://api.example.com/v1/deposits-securedcard/balance/increase/auto-fund" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "User-ID: USER_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "auto_fund_id": "af_123456789",
    "amount": 600.00,
    "enabled": true
  }'
```

**Response Example:**
```json
{
  "auto_fund_id": "af_123456789",
  "status": "ACTIVE",
  "amount": 600.00,
  "currency": "MXN",
  "frequency": "WEEKLY",
  "day_of_week": 1,
  "day_of_month": null,
  "source_account": "ACC123456789",
  "enabled": true,
  "created_at": "2023-03-15T12:00:00Z",
  "updated_at": "2023-03-15T13:00:00Z",
  "next_execution": "2023-03-20T00:00:00Z"
}
```

### UI Integration
- `GET /ui/home` - Retrieves data for the secured card home UI
  - Requires user authentication and UI services mandatory headers

**Curl Example:**
```bash
curl -X GET "https://api.example.com/v1/deposits-securedcard/ui/home" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "User-ID: USER_ID" \
  -H "Content-Type: application/json" \
  -H "Device-ID: DEVICE_ID" \
  -H "App-Version: 1.0.0"
```

**Response Example:**
```json
{
  "user": {
    "id": "USER_ID",
    "name": "John Doe",
    "email": "john.doe@example.com"
  },
  "secured_card": {
    "id": "CARD_123456789",
    "status": "ACTIVE",
    "balance": 1600.75,
    "currency": "MXN",
    "last_four_digits": "1234"
  },
  "recent_transactions": [
    {
      "id": "mov_123456789",
      "type": "DEPOSIT",
      "amount": 100.50,
      "currency": "MXN",
      "status": "COMPLETED",
      "created_at": "2023-03-15T10:30:00Z",
      "description": "Deposit to secured card"
    },
    {
      "id": "mov_987654321",
      "type": "WITHDRAWAL",
      "amount": 50.25,
      "currency": "MXN",
      "status": "COMPLETED",
      "created_at": "2023-03-14T15:45:00Z",
      "description": "Withdrawal from secured card"
    }
  ],
  "auto_funding": {
    "enabled": true,
    "amount": 600.00,
    "currency": "MXN",
    "frequency": "WEEKLY",
    "next_execution": "2023-03-20T00:00:00Z"
  }
}
```

## Architecture

The service is deployed on AWS using the following components:

- **ECS (Elastic Container Service)**: Hosts the application containers
- **NLB (Network Load Balancer)**: Distributes incoming traffic
- **DynamoDB**: Stores transaction and auto-fund data
- **Lambda**: Integrates with core banking systems
- **SNS**: Handles event publishing
- **CloudWatch**: Provides logging and monitoring

## Configuration

The service requires the following environment variables:

- `SERVICE_NAME`: Name of the service
- `ENV_STAGE_NAME`: Environment stage (dev, staging, prod)
- `AWS_REGION`: AWS region
- `AWS_ACCOUNT_ID`: AWS account ID
- `LOG_LEVEL`: Logging level
- `ECS_TASK_DEF_NAME`: ECS task definition name
- `PORT`: Container port
- `TRACE_SAMPLE_RATE`: Trace sampling rate
- `MOVEMENTS_CORE_LAMBDA_NAME`: Lambda function for core banking movements
- `SECURED_CARD_USER_TYPE`: User type for secured cards
- `INTERNAL_BASE_URL`: Internal base URL
- `EVENT_TOPIC_ARN`: SNS topic ARN for events
- `FRAUD_LAMBDA`: Lambda function for fraud detection
- `FRAUD_VERIFICATION_FLAG`: Flag for fraud verification
- `DYNAMO_TRANSACTIONS_TABLE`: DynamoDB table for transactions
- `DYNAMO_AUTO_FUND_TABLE`: DynamoDB table for auto-funding

## Development

### Prerequisites

- Go 1.19 or higher
- Docker
- AWS CLI configured with appropriate credentials

### Local Development

1. Clone the repository
2. Set up environment variables (copy from `.env.example` and modify as needed)
3. Run `make dev` to start the service locally

### Deployment

Use the provided deployment scripts to build and deploy the service to AWS:

```bash
./deploy.sh
```

## Troubleshooting

If you encounter the following error while running `make dev`:

```
Error saving credentials: error storing credentials – err: exec: "docker-credential-desktop": executable file not found in $PATH
```

You may need to clear up your existing docker store credential configurations. To fix it, remove the credStore section from the config file:

```json
{
  //remove this line
  "credsStore": "docker-desktop"
}
```

## GitHub Actions

In order to execute GitHub Actions in this repository, you will need to create a DevOps ticket requesting to add the **GitHub Actions Token**. Without this token, the test runner does not run correctly and the linter will fail if using libraries like `stori-utils-go`. This is important because you won't be able to merge into **main** due to branch protection.

## Warnings

AWS components do not support names with more than 32 characters. Be careful when naming your stack/service since stack-name and service-name are used for setting the name of the resources created by the template.
