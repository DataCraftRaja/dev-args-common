# Scalable Data Pipelines

Enterprise-grade data pipeline framework for batch, streaming, and ML workloads.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Sources  │───▶│  Ingestion Layer │───▶│  Processing     │
│  (DB, API,      │    │  (Kafka, Kinesis,│    │  (Spark, Flink, │
│   Files, CDC)   │    │   Pub/Sub)       │    │   Airflow)      │
└─────────────────┘    └──────────────────┘    └────────┬────────┘
                                                        │
┌─────────────────┐    ┌──────────────────┐    ┌────────▼────────┐
│   Data Sinks    │◀───│  Serving Layer   │◀───│  Storage        │
│  (Warehouse,    │    │  (API, Cache,    │    │  (Delta Lake,   │
│   Lakehouse,    │    │   Search, BI)    │    │   Iceberg,      │
│   Real-time)    │    │                  │    │   Hudi)         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Project Structure

```
├── .github/workflows/          # CI/CD pipelines
├── pipelines/
│   ├── batch/                  # Batch processing (Spark, Airflow)
│   ├── streaming/              # Real-time (Kafka, Flink, Spark Streaming)
│   └── ml/                     # ML pipelines
├── infrastructure/
│   ├── terraform/              # IaC for cloud resources
│   ├── kubernetes/             # K8s manifests
│   └── docker/                 # Dockerfiles
├── libs/
│   ├── common/                 # Shared utilities
│   ├── connectors/             # Source/sink connectors
│   └── transformations/        # Reusable transforms
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── configs/
│   ├── dev/
│   ├── staging/
│   └── prod/
├── docs/
├── scripts/
├── pyproject.toml
└── Makefile
```

## Quick Start

```bash
# Install dependencies
make install

# Run tests
make test

# Deploy to dev
make deploy-dev

# Run batch pipeline
make run-batch PIPELINE=example

# Run streaming pipeline
make run-streaming PIPELINE=example
```

## Pipeline Types

### Batch Pipelines
- **Orchestrator**: Apache Airflow
- **Engine**: Apache Spark / Databricks
- **Storage**: Delta Lake / Iceberg
- **Scheduling**: Cron / Event-driven

### Streaming Pipelines
- **Orchestrator**: Kubernetes / Flink SQL
- **Engine**: Apache Flink / Spark Structured Streaming
- **Message Queue**: Apache Kafka / Pulsar
- **State Backend**: RocksDB / S3

### ML Pipelines
- **Orchestrator**: Kubeflow / Airflow
- **Training**: PyTorch / TensorFlow / Spark MLlib
- **Serving**: KServe / Seldon / BentoML
- **Feature Store**: Feast / Hopsworks

## Configuration

Environment-specific configs in `configs/{dev,staging,prod}/`:
- `pipeline.yaml` - Pipeline definitions
- `infrastructure.yaml` - Resource specs
- `secrets.yaml` - Encrypted secrets (use SOPS/SealedSecrets)

## Testing Strategy

```bash
# Unit tests (fast, no external deps)
make test-unit

# Integration tests (with testcontainers)
make test-integration

# Contract tests (schema validation)
make test-contract

# Data quality tests
make test-data-quality
```

## Deployment

```bash
# Infrastructure
make tf-plan ENV=dev
make tf-apply ENV=dev

# Applications
make k8s-deploy ENV=dev
make helm-deploy ENV=dev
```

## Monitoring & Observability

- **Metrics**: Prometheus + Grafana
- **Logging**: ELK / Loki
- **Tracing**: Jaeger / Zipkin
- **Alerting**: Alertmanager / PagerDuty
- **Data Quality**: Great Expectations / Soda

## Contributing

1. Create feature branch from `development`
2. Make changes with tests
3. Run `make pre-commit`
4. Open PR to `development`
5. After review, merge to `development`
6. Release to `main` via release PR

## License

MIT License - see LICENSE file
