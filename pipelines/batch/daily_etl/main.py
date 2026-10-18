# Batch Pipeline Example - Daily ETL

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import argparse
import yaml
from pathlib import Path


def get_spark_session(app_name: str) -> SparkSession:
    """Create optimized Spark session for batch processing."""
    return SparkSession.builder \
        .appName(app_name) \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
        .getOrCreate()


def read_source(spark: SparkSession, config: dict):
    """Read data from source based on config."""
    source_config = config["source"]
    source_type = source_config["type"]
    
    if source_type == "jdbc":
        return spark.read \
            .format("jdbc") \
            .option("url", source_config["url"]) \
            .option("dbtable", source_config["table"]) \
            .option("user", source_config["user"]) \
            .option("password", source_config["password"]) \
            .option("driver", source_config.get("driver", "org.postgresql.Driver")) \
            .load()
    elif source_type == "parquet":
        return spark.read.parquet(source_config["path"])
    elif source_type == "delta":
        return spark.read.format("delta").load(source_config["path"])
    elif source_type == "csv":
        return spark.read \
            .option("header", "true") \
            .option("inferSchema", "true") \
            .csv(source_config["path"])
    else:
        raise ValueError(f"Unsupported source type: {source_type}")


def transform_data(df, config: dict):
    """Apply transformations based on config."""
    transforms = config.get("transformations", [])
    
    for transform in transforms:
        transform_type = transform["type"]
        
        if transform_type == "filter":
            df = df.filter(transform["condition"])
        elif transform_type == "select":
            df = df.select(*transform["columns"])
        elif transform_type == "with_column":
            df = df.withColumn(transform["name"], expr(transform["expression"]))
        elif transform_type == "group_by":
            df = df.groupBy(*transform["group_by"]).agg(*transform["aggregations"])
        elif transform_type == "join":
            other_df = read_source(spark, transform["other_source"])
            df = df.join(other_df, transform["on"], transform.get("how", "inner"))
        elif transform_type == "deduplicate":
            df = df.dropDuplicates(transform.get("subset"))
        elif transform_type == "watermark":
            df = df.withWatermark(transform["event_time"], transform["delay"])
    
    return df


def write_sink(df, config: dict):
    """Write data to sink based on config."""
    sink_config = config["sink"]
    sink_type = sink_config["type"]
    mode = sink_config.get("mode", "overwrite")
    
    writer = df.write.mode(mode)
    
    if sink_type == "jdbc":
        writer \
            .format("jdbc") \
            .option("url", sink_config["url"]) \
            .option("dbtable", sink_config["table"]) \
            .option("user", sink_config["user"]) \
            .option("password", sink_config["password"]) \
            .save()
    elif sink_type == "parquet":
        writer.parquet(sink_config["path"])
    elif sink_type == "delta":
        writer.format("delta").save(sink_config["path"])
    elif sink_type == "iceberg":
        writer.format("iceberg").save(sink_config["path"])
    elif sink_type == "csv":
        writer.option("header", "true").csv(sink_config["path"])
    else:
        raise ValueError(f"Unsupported sink type: {sink_type}")


def main():
    parser = argparse.ArgumentParser(description="Batch ETL Pipeline")
    parser.add_argument("--config", required=True, help="Path to pipeline config YAML")
    args = parser.parse_args()
    
    # Load configuration
    with open(args.config) as f:
        config = yaml.safe_load(f)
    
    pipeline_name = config["pipeline"]["name"]
    spark = get_spark_session(pipeline_name)
    
    try:
        # Read source data
        df = read_source(spark, config)
        print(f"Read {df.count()} records from source")
        
        # Apply transformations
        df = transform_data(df, config)
        print(f"After transformations: {df.count()} records")
        
        # Write to sink
        write_sink(df, config)
        print(f"Successfully wrote to sink")
        
    finally:
        spark.stop()


if __name__ == "__main__":
    main()