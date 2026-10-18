# Common Connectors for Data Sources/Sinks

"""Reusable connectors for various data sources and sinks."""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import *
from typing import Dict, Optional, Any
import json


class JDBCConnector:
    """JDBC connector for relational databases."""
    
    def __init__(self, spark: SparkSession, config: Dict[str, Any]):
        self.spark = spark
        self.config = config
    
    def read(self, table: str, predicates: Optional[list] = None) -> DataFrame:
        """Read from JDBC source."""
        reader = self.spark.read.format("jdbc") \
            .option("url", self.config["url"]) \
            .option("dbtable", table) \
            .option("user", self.config["user"]) \
            .option("password", self.config["password"]) \
            .option("driver", self.config.get("driver", "org.postgresql.Driver"))
        
        if predicates:
            reader = reader.option("predicates", predicates)
        
        return reader.load()
    
    def write(self, df: DataFrame, table: str, mode: str = "append") -> None:
        """Write to JDBC sink."""
        df.write.format("jdbc") \
            .option("url", self.config["url"]) \
            .option("dbtable", table) \
            .option("user", self.config["user"]) \
            .option("password", self.config["password"]) \
            .option("driver", self.config.get("driver", "org.postgresql.Driver")) \
            .mode(mode) \
            .save()


class KafkaConnector:
    """Kafka connector for streaming data."""
    
    def __init__(self, spark: SparkSession, config: Dict[str, Any]):
        self.spark = spark
        self.config = config
    
    def read_stream(self, topic: str, starting_offsets: str = "latest") -> DataFrame:
        """Read streaming data from Kafka."""
        return self.spark.readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", self.config["bootstrap_servers"]) \
            .option("subscribe", topic) \
            .option("startingOffsets", starting_offsets) \
            .option("failOnDataLoss", "false") \
            .load()
    
    def read_batch(self, topic: str, starting_offsets: str = "earliest", 
                   ending_offsets: str = "latest") -> DataFrame:
        """Read batch data from Kafka."""
        return self.spark.read \
            .format("kafka") \
            .option("kafka.bootstrap.servers", self.config["bootstrap_servers"]) \
            .option("subscribe", topic) \
            .option("startingOffsets", starting_offsets) \
            .option("endingOffsets", ending_offsets) \
            .load()
    
    def write_stream(self, df: DataFrame, topic: str, checkpoint_location: str) -> None:
        """Write streaming data to Kafka."""
        df.select(to_json(struct("*")).alias("value")) \
            .writeStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", self.config["bootstrap_servers"]) \
            .option("topic", topic) \
            .option("checkpointLocation", checkpoint_location) \
            .start()
    
    def write_batch(self, df: DataFrame, topic: str) -> None:
        """Write batch data to Kafka."""
        df.select(to_json(struct("*")).alias("value")) \
            .write \
            .format("kafka") \
            .option("kafka.bootstrap.servers", self.config["bootstrap_servers"]) \
            .option("topic", topic) \
            .save()


class S3Connector:
    """S3/MinIO connector for object storage."""
    
    def __init__(self, spark: SparkSession, config: Dict[str, Any]):
        self.spark = spark
        self.config = config
        self._configure_hadoop()
    
    def _configure_hadoop(self):
        """Configure Hadoop for S3 access."""
        hadoop_conf = self.spark.sparkContext._jsc.hadoopConfiguration()
        hadoop_conf.set("fs.s3a.access.key", self.config.get("access_key", ""))
        hadoop_conf.set("fs.s3a.secret.key", self.config.get("secret_key", ""))
        hadoop_conf.set("fs.s3a.endpoint", self.config.get("endpoint", "s3.amazonaws.com"))
        hadoop_conf.set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        hadoop_conf.set("fs.s3a.path.style.access", "true")
    
    def read_parquet(self, path: str) -> DataFrame:
        """Read Parquet files from S3."""
        return self.spark.read.parquet(f"s3a://{path}")
    
    def read_delta(self, path: str) -> DataFrame:
        """Read Delta table from S3."""
        return self.spark.read.format("delta").load(f"s3a://{path}")
    
    def read_iceberg(self, path: str) -> DataFrame:
        """Read Iceberg table from S3."""
        return self.spark.read.format("iceberg").load(f"s3a://{path}")
    
    def write_parquet(self, df: DataFrame, path: str, mode: str = "overwrite",
                      partition_by: Optional[list] = None) -> None:
        """Write Parquet files to S3."""
        writer = df.write.mode(mode)
        if partition_by:
            writer = writer.partitionBy(*partition_by)
        writer.parquet(f"s3a://{path}")
    
    def write_delta(self, df: DataFrame, path: str, mode: str = "overwrite",
                    partition_by: Optional[list] = None) -> None:
        """Write Delta table to S3."""
        writer = df.write.format("delta").mode(mode)
        if partition_by:
            writer = writer.partitionBy(*partition_by)
        writer.option("delta.autoOptimize.optimizeWrite", "true") \
            .option("delta.autoOptimize.autoCompact", "true") \
            .save(f"s3a://{path}")
    
    def write_iceberg(self, df: DataFrame, path: str, mode: str = "overwrite",
                      partition_by: Optional[list] = None) -> None:
        """Write Iceberg table to S3."""
        writer = df.write.format("iceberg").mode(mode)
        if partition_by:
            writer = writer.partitionBy(*partition_by)
        writer.save(f"s3a://{path}")


class FileConnector:
    """Local file system connector."""
    
    def __init__(self, spark: SparkSession):
        self.spark = spark
    
    def read_csv(self, path: str, header: bool = True, infer_schema: bool = True) -> DataFrame:
        """Read CSV files."""
        return self.spark.read \
            .option("header", str(header).lower()) \
            .option("inferSchema", str(infer_schema).lower()) \
            .csv(path)
    
    def read_json(self, path: str, multi_line: bool = False) -> DataFrame:
        """Read JSON files."""
        return self.spark.read \
            .option("multiLine", str(multi_line).lower()) \
            .json(path)
    
    def read_avro(self, path: str) -> DataFrame:
        """Read Avro files."""
        return self.spark.read.format("avro").load(path)
    
    def write_csv(self, df: DataFrame, path: str, mode: str = "overwrite",
                  header: bool = True) -> None:
        """Write CSV files."""
        df.write \
            .option("header", str(header).lower()) \
            .mode(mode) \
            .csv(path)
    
    def write_json(self, df: DataFrame, path: str, mode: str = "overwrite") -> None:
        """Write JSON files."""
        df.write.mode(mode).json(path)


def get_connector(connector_type: str, spark: SparkSession, config: Dict[str, Any]):
    """Factory function to get connector instance."""
    connectors = {
        "jdbc": JDBCConnector,
        "kafka": KafkaConnector,
        "s3": S3Connector,
        "file": FileConnector,
    }
    
    if connector_type not in connectors:
        raise ValueError(f"Unknown connector type: {connector_type}")
    
    if connector_type == "file":
        return connectors[connector_type](spark)
    
    return connectors[connector_type](spark, config)