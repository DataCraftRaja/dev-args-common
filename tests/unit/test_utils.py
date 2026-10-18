# Unit Tests for Common Utilities

"""Unit tests for common pipeline utilities."""

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import *

from libs.common.utils import (
    validate_schema,
    add_audit_columns,
    clean_column_names,
    cast_columns,
    hash_columns,
    fill_nulls,
    remove_outliers_iqr,
    cap_outliers,
)


@pytest.fixture(scope="session")
def spark():
    """Create Spark session for testing."""
    return SparkSession.builder \
        .appName("test") \
        .master("local[2]") \
        .config("spark.sql.shuffle.partitions", "2") \
        .getOrCreate()


@pytest.fixture
def sample_df(spark):
    """Create sample DataFrame for testing."""
    data = [
        ("1", "user1", "click", "2024-01-01 10:00:00", '{"page": "/home"}'),
        ("2", "user2", "purchase", "2024-01-01 11:00:00", '{"amount": "100"}'),
        ("3", "user3", "page_view", "2024-01-01 12:00:00", '{"page": "/product"}'),
    ]
    schema = StructType([
        StructField("event_id", StringType(), False),
        StructField("user_id", StringType(), False),
        StructField("event_type", StringType(), False),
        StructField("event_timestamp", StringType(), False),
        StructField("properties", StringType(), True),
    ])
    return spark.createDataFrame(data, schema)


class TestValidateSchema:
    """Tests for validate_schema function."""
    
    def test_valid_schema(self, spark, sample_df):
        expected = StructType([
            StructField("event_id", StringType(), False),
            StructField("user_id", StringType(), False),
        ])
        assert validate_schema(sample_df.select("event_id", "user_id"), expected)
    
    def test_missing_column(self, spark, sample_df):
        expected = StructType([
            StructField("event_id", StringType(), False),
            StructField("missing_col", StringType(), False),
        ])
        assert not validate_schema(sample_df, expected)
    
    def test_type_mismatch(self, spark, sample_df):
        expected = StructType([
            StructField("event_id", IntegerType(), False),  # Wrong type
        ])
        assert not validate_schema(sample_df.select("event_id"), expected)


class TestAddAuditColumns:
    """Tests for add_audit_columns function."""
    
    def test_adds_all_columns(self, spark, sample_df):
        result = add_audit_columns(sample_df, "test_pipeline", "run_123")
        
        assert "_pipeline_name" in result.columns
        assert "_run_id" in result.columns
        assert "_processed_at" in result.columns
        assert "_source_file" in result.columns
        
        row = result.first()
        assert row._pipeline_name == "test_pipeline"
        assert row._run_id == "run_123"


class TestCleanColumnNames:
    """Tests for clean_column_names function."""
    
    def test_cleans_special_chars(self, spark):
        df = spark.createDataFrame([(1, 2)], ["Column Name", "Another-Column"])
        result = clean_column_names(df)
        assert result.columns == ["column_name", "another_column"]
    
    def test_handles_duplicates(self, spark):
        df = spark.createDataFrame([(1, 2)], ["col", "col"])
        result = clean_column_names(df)
        assert len(result.columns) == 2
        assert result.columns[0] != result.columns[1]


class TestCastColumns:
    """Tests for cast_columns function."""
    
    def test_casts_string_to_int(self, spark):
        df = spark.createDataFrame([("1",), ("2",)], ["value"])
        result = cast_columns(df, {"value": IntegerType()})
        assert result.schema["value"].dataType == IntegerType()
        assert result.first().value == 1


class TestHashColumns:
    """Tests for hash_columns function."""
    
    def test_creates_hash(self, spark, sample_df):
        result = hash_columns(sample_df, ["event_id", "user_id"])
        assert "row_hash" in result.columns
        assert result.first().row_hash is not None
    
    def test_consistent_hash(self, spark, sample_df):
        result1 = hash_columns(sample_df, ["event_id", "user_id"])
        result2 = hash_columns(sample_df, ["event_id", "user_id"])
        assert result1.first().row_hash == result2.first().row_hash


class TestFillNulls:
    """Tests for fill_nulls function."""
    
    def test_fills_nulls(self, spark):
        df = spark.createDataFrame([(1, None), (None, "test")], ["a", "b"])
        result = fill_nulls(df, {"a": 0, "b": "default"})
        assert result.filter(col("a").isNull()).count() == 0
        assert result.filter(col("b").isNull()).count() == 0


class TestOutlierHandling:
    """Tests for outlier detection and handling."""
    
    def test_remove_outliers_iqr(self, spark):
        # Data with clear outliers
        data = [1, 2, 3, 4, 5, 100, 200]  # 100, 200 are outliers
        df = spark.createDataFrame([(x,) for x in data], ["value"])
        result = remove_outliers_iqr(df, "value")
        assert result.count() == 5  # Only 1-5 remain
    
    def test_cap_outliers(self, spark):
        data = [1, 2, 3, 4, 5, 100, 200]
        df = spark.createDataFrame([(x,) for x in data], ["value"])
        result = cap_outliers(df, "value", 0.0, 1.0)  # Cap at min/max
        max_val = result.agg(max("value")).first()[0]
        assert max_val == 5  # Capped at 99th percentile (5)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])