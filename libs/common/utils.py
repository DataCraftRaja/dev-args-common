# Common Utilities for Data Pipelines

"""Shared utilities for data pipeline operations."""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from typing import Dict, List, Optional, Any
import logging
from functools import wraps
import time


def get_logger(name: str) -> logging.Logger:
    """Get configured logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def timer(func):
    """Decorator to time function execution."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logger = get_logger(func.__module__)
        logger.info(f"{func.__name__} completed in {elapsed:.2f}s")
        return result
    return wrapper


def read_config(config_path: str) -> Dict[str, Any]:
    """Read YAML configuration file."""
    import yaml
    with open(config_path) as f:
        return yaml.safe_load(f)


def validate_schema(df: DataFrame, expected_schema: StructType) -> bool:
    """Validate DataFrame schema matches expected schema."""
    actual_fields = {f.name: f.dataType for f in df.schema.fields}
    expected_fields = {f.name: f.dataType for f in expected_schema.fields}
    
    missing = set(expected_fields) - set(actual_fields)
    extra = set(actual_fields) - set(expected_fields)
    type_mismatch = {
        k: (actual_fields[k], expected_fields[k])
        for k in set(actual_fields) & set(expected_fields)
        if actual_fields[k] != expected_fields[k]
    }
    
    if missing or extra or type_mismatch:
        logger = get_logger(__name__)
        if missing:
            logger.error(f"Missing columns: {missing}")
        if extra:
            logger.warning(f"Extra columns: {extra}")
        if type_mismatch:
            logger.error(f"Type mismatches: {type_mismatch}")
        return False
    return True


def add_audit_columns(df: DataFrame, pipeline_name: str, run_id: str) -> DataFrame:
    """Add standard audit columns to DataFrame."""
    return df \
        .withColumn("_pipeline_name", lit(pipeline_name)) \
        .withColumn("_run_id", lit(run_id)) \
        .withColumn("_processed_at", current_timestamp()) \
        .withColumn("_source_file", input_file_name())


def write_delta_table(
    df: DataFrame,
    path: str,
    mode: str = "overwrite",
    partition_by: Optional[List[str]] = None,
    optimize_write: bool = True,
    auto_compact: bool = True
) -> None:
    """Write DataFrame as Delta table with optimizations."""
    writer = df.write.format("delta").mode(mode)
    
    if partition_by:
        writer = writer.partitionBy(*partition_by)
    
    if optimize_write:
        writer = writer.option("delta.autoOptimize.optimizeWrite", "true")
    if auto_compact:
        writer = writer.option("delta.autoOptimize.autoCompact", "true")
    
    writer.save(path)


def read_delta_table(spark: SparkSession, path: str, version: Optional[int] = None) -> DataFrame:
    """Read Delta table with optional version."""
    reader = spark.read.format("delta")
    if version is not None:
        reader = reader.option("versionAsOf", version)
    return reader.load(path)


def merge_delta_table(
    spark: SparkSession,
    target_path: str,
    source_df: DataFrame,
    merge_condition: str,
    update_condition: Optional[str] = None,
    delete_condition: Optional[str] = None
) -> None:
    """Perform MERGE operation on Delta table."""
    from delta.tables import DeltaTable
    
    target_table = DeltaTable.forPath(spark, target_path)
    
    merge_builder = target_table.alias("target").merge(
        source_df.alias("source"),
        merge_condition
    )
    
    if update_condition:
        merge_builder = merge_builder.whenMatchedUpdate(
            condition=update_condition,
            set={c: col(f"source.{c}") for c in source_df.columns}
        )
    else:
        merge_builder = merge_builder.whenMatchedUpdateAll()
    
    if delete_condition:
        merge_builder = merge_builder.whenMatchedDelete(condition=delete_condition)
    
    merge_builder = merge_builder.whenNotMatchedInsertAll()
    
    merge_builder.execute()


def get_table_history(spark: SparkSession, path: str, limit: int = 10) -> DataFrame:
    """Get Delta table history."""
    from delta.tables import DeltaTable
    table = DeltaTable.forPath(spark, path)
    return table.history(limit)


def vacuum_table(spark: SparkSession, path: str, retention_hours: int = 168) -> None:
    """Vacuum Delta table to remove old files."""
    from delta.tables import DeltaTable
    table = DeltaTable.forPath(spark, path)
    table.vacuum(retention_hours)


# Schema definitions for common entities
USER_EVENT_SCHEMA = StructType([
    StructField("event_id", StringType(), False),
    StructField("user_id", StringType(), False),
    StructField("event_type", StringType(), False),
    StructField("event_timestamp", TimestampType(), False),
    StructField("properties", MapType(StringType(), StringType()), True),
])

USER_PROFILE_SCHEMA = StructType([
    StructField("user_id", StringType(), False),
    StructField("email", StringType(), True),
    StructField("first_name", StringType(), True),
    StructField("last_name", StringType(), True),
    StructField("created_at", TimestampType(), False),
    StructField("updated_at", TimestampType(), False),
    StructField("is_active", BooleanType(), True),
])

TRANSACTION_SCHEMA = StructType([
    StructField("transaction_id", StringType(), False),
    StructField("user_id", StringType(), False),
    StructField("amount", DecimalType(10, 2), False),
    StructField("currency", StringType(), False),
    StructField("status", StringType(), False),
    StructField("created_at", TimestampType(), False),
    StructField("completed_at", TimestampType(), True),
])