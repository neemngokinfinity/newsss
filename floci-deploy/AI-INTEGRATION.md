# Floci — AI Integration

Use the emulator like AWS, pointing clients at `http://127.0.0.1:4566`.

## Environment

```bash
export AWS_ENDPOINT_URL=http://127.0.0.1:4566
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
```

## S3 (Python boto3)

```python
import boto3
s3 = boto3.client("s3", endpoint_url="http://127.0.0.1:4566")
s3.create_bucket(Bucket="ai-assets")
s3.put_object(Bucket="ai-assets", Key="prompt.txt", Body=b"hello")
```

## DynamoDB (boto3)

```python
import boto3
client = boto3.client("dynamodb", endpoint_url="http://127.0.0.1:4566")
client.create_table(TableName="jobs", KeySchema=[{"AttributeName":"id","KeyType":"HASH"}],
    AttributeDefinitions=[{"AttributeName":"id","AttributeType":"S"}],
    BillingMode="PAY_PER_REQUEST")
```

## SQS

```bash
aws --endpoint-url=http://127.0.0.1:4566 sqs create-queue --queue-name jobs
```

## Lambda (Docker executor)

```bash
# Ensure FLOCI_LAMBDA_EXECUTOR=docker and socket mounted.
# Deploy a function package (zip) with aws lambda create-function,
# pointing --endpoint-url at 127.0.0.1:4566.
```

## Secrets Manager

```bash
aws --endpoint-url=http://127.0.0.1:4566 secretsmanager create-secret \
  --name ai/litellm --secret-string '{"api_key":"sk-test"}'
```

All values are fake; never put real keys here. See [SECURITY.md](SECURITY.md).
