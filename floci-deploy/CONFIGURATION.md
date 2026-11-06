# Floci — Configuration

## Environment (.env)

| Variable | Default | Meaning |
|---|---|---|---|
| `FLOCI_AUTH_STRING` | `test:test` | Basic auth user:pass for API/console |
| `AWS_ACCESS_KEY_ID` | `test` | Dummy access key (emulated) |
| `AWS_SECRET_ACCESS_KEY` | `test` | Dummy secret key (emulated) |
| `AWS_DEFAULT_REGION` | `us-east-1` | Default region |
| `FLOCI_INSECURE` | `1` | Skip cert checks for the emulator |
| `FLOCI_AWS_EXECUTABLE` | `aws` | AWS CLI path used by emulator |
| `FLOCI_DATA_DIR` | `/opt/floci/data` | Internal data dir (volume) |
| `FLOCI_HOME` | `/root` | Emulator home |
| `FLOCI_LAMBDA_EXECUTOR` | `docker` | Lambda runs in real Docker containers |
| `FLOCI_SERVICES` | (long list) | Comma-separated enabled services |

## Ports (all bound to loopback 127.0.0.1)

| Port | Service |
|---|---|---|
| 4566 | Primary AWS API endpoint |
| 4500 | Web console / health (sidecar probe) |
| 6379 | ElastiCache (Redis) proxy |
| 6400 | MemoryDB proxy |
| 7001 | RDS proxy (PostgreSQL/MySQL) |
| 8182 | Neptune Gremlin proxy |

Never expose these publicly; connect via VPN / tunnel where needed.

## Storage modes

- Default: persistent bind to volume `floci-data`.
- Temp: use `tmpfs` (already mounted at `/tmp`, `/opt/floci/tmp`) for throwaway runs.

## Client usage pattern

```bash
export AWS_ENDPOINT_URL=http://127.0.0.1:4566
export AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
export AWS_AUTH_STRING=test:test
# then use `aws` or SDKs as usual
```

See [AI-INTEGRATION.md](AI-INTEGRATION.md) for SDK/CLI examples.
