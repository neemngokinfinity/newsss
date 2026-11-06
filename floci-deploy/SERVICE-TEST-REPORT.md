# Floci — Service Test Report

Date: 2026-11-06. Host: VPS. Image `floci/floci:2.4.0`.

## Core (15/15 passed)

- s3: bucket create / put-object / list-objects ✓
- dynamodb: create-table / put-item / get-item ✓
- sqs: create-queue / send-message / receive-message ✓
- iam: create-user / attach policy ✓
- sts: get-caller-identity ✓
- secretsmanager: create-secret / get-secret-value ✓
- cloudwatch/logs: log-group / put-log-events ✓
- events: put-rule / put-targets ✓
- apigateway: create-rest-api ✓
- lambda: create-function (docker executor) ✓
- opensearch: create-index ✓
- kinesis: create-stream ✓
- sns: create-topic ✓
- cognito: create-user-pool ✓
- es: create-index ✓

## Heavy (4/4 passed)

- neptune (gremlin) 8182 ✓
- rds 7001 ✓
- elasticache 6379 ✓
- memorydb 6400 ✓

## Health marker

`curl -s http://127.0.0.1:4566/_localstack/health` → all "available".
Log line `=== AWS Local Emulator Ready ===` observed.
