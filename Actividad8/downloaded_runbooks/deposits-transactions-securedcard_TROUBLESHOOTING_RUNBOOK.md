# Troubleshooting Guide & Runbook

## Overview

This guide helps engineers troubleshoot issues in the `deposits-transactions-securedcard` service using structured logs, AWS CloudWatch, and best practices. It covers:
- Log message origins and meanings
- How to search for issues by UserID or RequestID
- Common causes and next steps for each log/error
- Example CloudWatch queries
- Monitoring Dashboards:
  - Main Service Dashboard: https://grafana-v9.storicardprod.com/d/f22ca18e-db1a-4024-a142-5e15fdec321a/txns-secured-card?orgId=1
  - Key Metrics:
    - Transaction Success Rate
    - API Latency & Error Rates  
    - Lambda Invocations & Duration
    - Database Connection Pool Stats

---

## 1. Logging Structure

### a. Contextual Logging

Handlers and use cases use structured logging with context:
```go
internalLogger := r.logger.With("user", userID, "product_request_id", requestID)
```
This ensures every log entry can be traced to a user and request.

### b. LogWithMetrics

Most logs use:
```go
log.LogWithMetrics(logger, "<event_key>", <status_code>, log.TurboLambda).<Level>("message", "key", value, ...)
```
- `<event_key>`: Unique identifier for the log event (e.g., `self-out-processDecreaseTxn-unreadableRequest`)
- `<Level>`: `.Errorw`, `.Warnw`, `.Infow`, etc.

Example to search:

```sql
fields @timestamp, @message
| parse @message '"level":"*"' as level
| filter level = "error"
```

---

## 2. How to Search Logs in AWS CloudWatch

### a. By UserID or RequestID

To search logs by UserID or RequestID, follow these steps:

1. Navigate to CloudWatch Logs Insights:
   https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:logs-insights

2. Enter the name prefix for your service logs:
   ![Select Log Group Name Interface](/runbook-images/select_log_group_name.png)


3. In the log groups selection interface:
   - Click on "Name prefix" 
   - Select the following log groups:
     - `/aws/lambda/deposits-secured`
     - `/aws/ecs/deposits-securedcard`

    ![Enter Name Prefix Example](/runbook-images/name_prefix.png)
   
   This will allow you to search across both the Lambda and ECS service logs.

4. In the query editor, paste and customize this query:
   ![Query Example](/runbook-images/example.png)

   ```sql
    fields @timestamp, @message, @logStream, @log
    | filter @message like /<user_id>/
    | sort @timestamp desc
    ```

### b. By Event Key

To find all logs for a specific event (e.g., a failed decrease transaction):
```sql
fields @timestamp, @message, @logStream, @log
| filter @message like /self-out-processDecreaseTxn-unreadableRequest/
| sort @timestamp desc
```

---

## 3. Log Event Reference

Below are key log events, their origins, possible causes, and recommended actions.

---

### Decrease Balance Handler (`decrease_balance.go`)

| Event Key | Log Level | Where | Message | Possible Causes | Next Steps |
|-----------|-----------|-------|---------|----------------|------------|
| self-out-processDecreaseTxn-unreadableRequest | Error | Handler | Error reading or unmarshalling request body | Malformed JSON, empty body, client error | Check client request, validate JSON |
| self-out-processDecreaseTxn-fieldValidatorError | Error | Handler | Validation failed for request fields | Missing/invalid fields | Check request payload, update client |
| self-out-processDecreaseTxn-successRequest | Info | Handler | Transaction processed successfully | - | No action needed |

#### Example CloudWatch Query
```sql
fields @timestamp, @message
| filter @message like /self-out-processDecreaseTxn-unreadableRequest/
| sort @timestamp desc
```

---

### Increase Balance Handler (`increase_balance.go`)

| Event Key | Log Level | Where | Message | Possible Causes | Next Steps |
|-----------|-----------|-------|---------|----------------|------------|
| self-out-processIncreaseTxn-unreadableRequest | Error | Handler | Error reading or unmarshalling request body | Malformed JSON, empty body | Check client request, validate JSON |
| self-out-processIncreaseTxn-fieldValidatorError | Error | Handler | Validation failed for request fields | Missing/invalid fields | Check request payload, update client |
| self-out-processIncreaseTxn-successRequest | Warn | Handler | Transaction processed successfully | - | No action needed |

---

### Auto-Fund Handler (`secure_card_auto_fund.go`)

| Event Key | Log Level | Where | Message | Possible Causes | Next Steps |
|-----------|-----------|-------|---------|----------------|------------|
| auto-fund-transaction-success | Info | Handler | Transaction processed | - | No action needed |

---

### Use Case & Adapter Logs

Many use cases and adapters emit logs with event keys like:
- `self-out-decrease-balance-error`
- `self-out-increase-balance-error`
- `self-out-getBalance-card-data-error`
- `auto-fund-get-error`
- `core-banking-adjust-credit-line-request-error`
- `fraud-validate-operation-marshal-error`

#### For each:
- **Origin**: See the event key and file name.
- **Possible Causes**: Usually external system errors, validation failures, or business rule violations.
- **Next Steps**: Check the error message, trace the request by UserID/RequestID, and review upstream/downstream dependencies.

---

## 4. Best Practices

- Always include `user` and `product_request_id` in logs for traceability.
- Use unique event keys for each log point.
- For errors, check both the event key and the error message for root cause.
- Use CloudWatch queries to filter by event key, UserID, or RequestID.
- For recurring issues, correlate logs across handlers and use cases.


---

## 5. Adding New Log Events

- Use `log.LogWithMetrics` with a unique event key.
- Always include context: user, request ID, and relevant business data.
- Document new event keys in this runbook.

---

## 6. Exhaustive Log Event Reference (Partial Update)

| Event Key / Message                                 | Log Level | File                                 | Function                | Example Message                        | Typical Causes                | Next Steps                |
|-----------------------------------------------------|-----------|--------------------------------------|-------------------------|----------------------------------------|------------------------------|---------------------------|
| core-banking-adjust-credit-line-marshal-error       | Error     | adapters/http/core/corebanking.go    | AdjustCreditLine        | Error converting body to JSON           | Malformed request body        | Check request payload     |
| core-banking-adjust-credit-line-request-error       | Error     | adapters/http/core/corebanking.go    | AdjustCreditLine        | http request                           | Network/API error             | Check downstream service  |
| core-banking-adjust-credit-line-unmarshal-error     | Error     | adapters/http/core/corebanking.go    | AdjustCreditLine        | JsonResponseUnmarshalling              | Invalid JSON response         | Check upstream service    |
| core-banking-adjust-credit-line-success             | Info      | adapters/http/core/corebanking.go    | AdjustCreditLine        | Credit line adjusted successfully       | -                            | No action needed          |
| core-banking-get-credit-line-request-error          | Error     | adapters/http/core/corebanking.go    | GetCreditLine           | http request                           | Network/API error             | Check downstream service  |
| core-banking-get-credit-line-unmarshal-error        | Error     | adapters/http/core/corebanking.go    | GetCreditLine           | JsonResponseUnmarshalling              | Invalid JSON response         | Check upstream service    |
| core-banking-get-credit-line-success                | Info      | adapters/http/core/corebanking.go    | GetCreditLine           | Credit line retrieved successfully      | -                            | No action needed          |
| error creating request                              | Error     | adapters/http/core/corebanking.go    | doRequestWithMetrics    | error creating request                  | Malformed HTTP request        | Check request parameters  |
| error sending request                               | Error     | adapters/http/core/corebanking.go    | doRequestWithMetrics    | error sending request                   | Network error                 | Check network/API         |
| error closing response body                         | Error     | adapters/http/core/corebanking.go    | doRequestWithMetrics    | error closing response body             | IO error                      | Check server/response     |
| error reading response body                         | Error     | adapters/http/core/corebanking.go    | doRequestWithMetrics    | error reading response body             | IO error                      | Check server/response     |
| non-2xx status code                                 | Error     | adapters/http/core/corebanking.go    | doRequestWithMetrics    | non-2xx status code                     | Upstream error                | Check upstream service    |
| http request to centro accounts in stori api        | Error     | adapters/http/core/corebanking.go    | GetAccounts             | http request to centro accounts in stori api | Network/API error        | Check downstream service  |
| JsonResponseUnmarshalling                           | Error     | adapters/http/core/corebanking.go    | GetAccounts, GetCards, GetCalculations | JsonResponseUnmarshalling | Invalid JSON response         | Check upstream service    |
| http request to stori core api calculations         | Error     | adapters/http/core/corebanking.go    | GetCalculations         | http request to stori core api calculations | Network/API error         | Check downstream service  |
| http request to cards api failed                    | Error     | adapters/http/core/corebanking.go    | GetCards                | http request to cards api failed        | Network/API error             | Check downstream service  |

---

### Decrease Balance Handler (src/app/infrastructure/handler/decrease_balance.go)

| Event Key / Message                              | Log Level | File                                         | Function                    | Example Message                        | Typical Causes                | Next Steps                |
|--------------------------------------------------|-----------|----------------------------------------------|-----------------------------|----------------------------------------|------------------------------|---------------------------|
| self-out-processDecreaseTxn-unreadableRequest    | Error     | infrastructure/handler/decrease_balance.go   | DecreaseUserVaultBalance    | BindErrorLogger                        | Malformed JSON, empty body    | Check client request, validate JSON |
| self-out-processDecreaseTxn-fieldValidatorError  | Error     | infrastructure/handler/decrease_balance.go   | DecreaseUserVaultBalance    | ValidatorErrorLogger                    | Missing/invalid fields        | Check request payload, update client |
| self-out-processDecreaseTxn-successRequest       | Info      | infrastructure/handler/decrease_balance.go   | DecreaseUserVaultBalance    | secured_card_decrease_txn_processed     | -                            | No action needed          |

---

### Increase Balance Handler (src/app/infrastructure/handler/increase_balance.go)

| Event Key / Message                              | Log Level | File                                         | Function                    | Example Message                        | Typical Causes                | Next Steps                |
|--------------------------------------------------|-----------|----------------------------------------------|-----------------------------|----------------------------------------|------------------------------|---------------------------|
| self-out-processIncreaseTxn-unreadableRequest    | Error     | infrastructure/handler/increase_balance.go   | IncreaseUserVaultBalance    | BindErrorLogger                        | Malformed JSON, empty body    | Check client request, validate JSON |
| self-out-processIncreaseTxn-fieldValidatorError  | Error     | infrastructure/handler/increase_balance.go   | IncreaseUserVaultBalance    | ValidatorErrorLogger                    | Missing/invalid fields        | Check request payload, update client |
| self-out-processIncreaseTxn-successRequest       | Warn      | infrastructure/handler/increase_balance.go   | IncreaseUserVaultBalance    | secured_card_increase_txn_processed     | -                            | No action needed          |

---

### Secure Card Auto Fund Handler (src/app/infrastructure/handler/secure_card_auto_fund.go)

| Event Key / Message              | Log Level | File                                              | Function             | Example Message              | Typical Causes         | Next Steps           |
|----------------------------------|-----------|---------------------------------------------------|----------------------|------------------------------|-----------------------|----------------------|
| auto-fund-transaction-success    | Info      | infrastructure/handler/secure_card_auto_fund.go   | CreateNewAutoFund    | Transaction processed        | -                     | No action needed     |
| No body provided, will use default values | Info | infrastructure/handler/secure_card_auto_fund.go | CreateNewAutoFund    | No body provided, will use default values | Empty request body | Check client request |
| failed to decode JSON request body | Error    | infrastructure/handler/secure_card_auto_fund.go   | CreateNewAutoFund, UpdateAutoFund | failed to decode JSON request body | Malformed JSON, client error | Check client request, validate JSON |
| empty request body               | Error     | infrastructure/handler/secure_card_auto_fund.go   | UpdateAutoFund       | empty request body           | Empty request body     | Check client request |

---

### Decrease Balance Use Case (src/app/application/decrease_balance_use_case.go)

| Event Key / Message                   | Log Level | File                                         | Function                    | Example Message                              | Typical Causes                | Next Steps                |
|---------------------------------------|-----------|----------------------------------------------|-----------------------------|----------------------------------------------|------------------------------|---------------------------|
| self-out-decrease-balance-start       | Info      | application/decrease_balance_use_case.go     | Execute                     | starting decrease balance transaction        | Start of transaction          | Trace transaction flow     |
| self-out-decrease-balance-error       | Error     | application/decrease_balance_use_case.go     | Execute                     | failed to process decrease balance transaction | Downstream or business error | Check error details, dependencies |
| self-out-decrease-balance-success     | Info      | application/decrease_balance_use_case.go     | Execute                     | successfully processed decrease balance transaction | -                        | No action needed          |

---

### Increase Balance Use Case (src/app/application/increase_balance_use_case.go)

| Event Key / Message                        | Log Level | File                                         | Function                    | Example Message                              | Typical Causes                | Next Steps                |
|--------------------------------------------|-----------|----------------------------------------------|-----------------------------|----------------------------------------------|------------------------------|---------------------------|
| self-out-increase-balance-unknown-trigger  | Info      | application/increase_balance_use_case.go     | Execute                     | using default trigger value                  | Missing trigger info          | Check request source       |
| self-out-increase-balance-start            | Info      | application/increase_balance_use_case.go     | Execute                     | starting increase balance transaction        | Start of transaction          | Trace transaction flow     |
| self-out-increase-balance-error            | Error     | application/increase_balance_use_case.go     | Execute                     | failed to process increase balance transaction | Downstream or business error | Check error details, dependencies |
| self-out-increase-balance-success          | Info      | application/increase_balance_use_case.go     | Execute                     | successfully processed increase balance transaction | -                        | No action needed          |

---

### Modify Balance Use Case (src/app/application/modify_balance_use_case.go)

| Event Key / Message                                   | Log Level | File                                         | Function                    | Example Message                              | Typical Causes                | Next Steps                |
|------------------------------------------------------|-----------|----------------------------------------------|-----------------------------|----------------------------------------------|------------------------------|---------------------------|
| self-out-processModifyCreditLine-card-data-error     | Error     | application/modify_balance_use_case.go       | Execute                     | error getting card data                      | Card data fetch error         | Check card data service    |
| self-out-processModifyCreditLine-fraud-validation-error | Error  | application/modify_balance_use_case.go       | Execute                     | fraud validation error                       | Fraud engine error            | Check fraud engine         |
| self-out-processModifyCreditLine-fraud-rejected      | Warn      | application/modify_balance_use_case.go       | Execute                     | transaction rejected by fraud                | Fraud engine rejected         | Review fraud rules         |
| self-out-processModifyCreditLine-core-banking-error  | Error/Warn| application/modify_balance_use_case.go       | Execute                     | error getting/adjusting calculations         | Core banking error            | Check core banking         |
| self-out-processModifyCreditLine-cast-error          | Error     | application/modify_balance_use_case.go       | Execute                     | failed to cast calculations.Data             | Data type mismatch            | Check data structure       |
| self-out-getBalance-core-banking-error              | Error     | application/modify_balance_use_case.go       | Execute                     | error getting credit line                    | Core banking error            | Check core banking         |
| self-out-getBalance-cast-error                      | Error     | application/modify_balance_use_case.go       | Execute                     | failed to cast getBalanceRes.Data            | Data type mismatch            | Check data structure       |
| self-out-processModifyCreditLine-sns-publish        | Info      | application/modify_balance_use_case.go       | Execute                     | published event to SNS                       | -                            | No action needed           |
| self-out-processModifyCreditLine-response-format-error | Warn    | application/modify_balance_use_case.go       | Execute                     | format_credit_limit_failed                   | Response formatting error     | Check formatting logic     |
| self-out-processModifyCreditLine-success            | Info      | application/modify_balance_use_case.go       | Execute                     | successfully processed modify credit line    | -                            | No action needed           |

---

### Create Auto Fund Use Case (src/app/application/sc_create_auto_fund_use_case.go)

| Event Key / Message                        | Log Level | File                                         | Function                    | Example Message                              | Typical Causes                | Next Steps                |
|--------------------------------------------|-----------|----------------------------------------------|-----------------------------|----------------------------------------------|------------------------------|---------------------------|
| self-out-create-auto-fund-start            | Info      | application/sc_create_auto_fund_use_case.go  | Execute                     | starting auto-fund transaction processing    | Start of transaction          | Trace transaction flow     |
| self-out-create-auto-fund-card-data-error  | Error     | application/sc_create_auto_fund_use_case.go  | Execute                     | error getting card data                      | Card data fetch error         | Check card data service    |
| self-out-create-auto-fund-secured-user     | Info      | application/sc_create_auto_fund_use_case.go  | Execute                     | is a secured card user, will process         | -                            | No action needed           |
| self-out-create-auto-fund-not-secured-user | Info      | application/sc_create_auto_fund_use_case.go  | Execute                     | is not a secured card user, will not process | Not a secured card user       | Check user eligibility     |
| self-out-create-auto-fund-already-exists   | Info      | application/sc_create_auto_fund_use_case.go  | Execute                     | found existing auto-fund configuration       | Auto-fund already exists      | No action needed           |
| self-out-create-auto-fund-check-error      | Error     | application/sc_create_auto_fund_use_case.go  | Execute                     | failed to check for existing auto-fund       | Repository error              | Check repository           |
| self-out-create-auto-fund-error            | Error     | application/sc_create_auto_fund_use_case.go  | Execute                     | failed to create auto-fund                   | Repository error              | Check repository           |
| self-out-create-auto-fund-success          | Info      | application/sc_create_auto_fund_use_case.go  | Execute                     | successfully created auto-fund configuration | -                            | No action needed           |

---

### Get Auto Fund Use Case (src/app/application/sc_get_auto_fund_use_case.go)

| Event Key / Message                        | Log Level | File                                         | Function                    | Example Message                              | Typical Causes                | Next Steps                |
|--------------------------------------------|-----------|----------------------------------------------|-----------------------------|----------------------------------------------|------------------------------|---------------------------|
| self-out-get-auto-fund-start               | Info      | application/sc_get_auto_fund_use_case.go     | Execute                     | starting get auto-fund processing            | Start of transaction          | Trace transaction flow     |
| self-out-get-auto-fund-not-found           | Info      | application/sc_get_auto_fund_use_case.go     | Execute                     | auto-fund configuration not found            | No auto-fund for user         | Check user setup           |
| self-out-get-auto-fund-error               | Error     | application/sc_get_auto_fund_use_case.go     | Execute                     | failed to retrieve auto-fund configuration   | Repository or DB error         | Check repository/DB        |
| self-out-get-auto-fund-success             | Info      | application/sc_get_auto_fund_use_case.go     | Execute                     | successfully retrieved auto-fund configuration | -                            | No action needed           |

--- 