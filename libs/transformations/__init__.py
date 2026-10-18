# Reusable Transformations for Data Pipelines

"""Common data transformations used across pipelines."""

from pyspark.sql import DataFrame
from pyspark.sql.functions import *
from pyspark.sql.types import *
from typing import List, Dict, Optional, Any
import re


def clean_column_names(df: DataFrame) -> DataFrame:
    """Clean column names: lowercase, replace spaces/special chars with underscore."""
    new_columns = []
    for col_name in df.columns:
        # Replace non-alphanumeric with underscore
        clean = re.sub(r'[^a-zA-Z0-9_]', '_', col_name)
        # Remove leading/trailing underscores
        clean = clean.strip('_')
        # Lowercase
        clean = clean.lower()
        # Handle duplicates
        base = clean
        counter = 1
        while clean in new_columns:
            clean = f"{base}_{counter}"
            counter += 1
        new_columns.append(clean)
    
    return df.toDF(*new_columns)


def cast_columns(df: DataFrame, column_types: Dict[str, DataType]) -> DataFrame:
    """Cast columns to specified types."""
    for col_name, data_type in column_types.items():
        if col_name in df.columns:
            df = df.withColumn(col_name, col(col_name).cast(data_type))
    return df


def parse_json_column(df: DataFrame, column: str, schema: StructType) -> DataFrame:
    """Parse JSON string column into structured columns."""
    return df.withColumn(column, from_json(col(column), schema))


def flatten_struct(df: DataFrame, struct_column: str, prefix: str = "") -> DataFrame:
    """Flatten a struct column into individual columns."""
    struct_fields = df.schema[struct_column].dataType.fields
    field_names = [f.name for f in struct_fields]
    
    select_exprs = [c for c in df.columns if c != struct_column]
    for field in field_names:
        select_exprs.append(col(f"{struct_column}.{field}").alias(f"{prefix}{field}"))
    
    return df.select(*select_exprs)


def explode_array(df: DataFrame, array_column: str, 
                  element_alias: str = "element",
                  index_alias: str = "index") -> DataFrame:
    """Explode array column with optional index."""
    return df.withColumn(element_alias, explode(col(array_column))) \
             .withColumn(index_alias, posexplode(col(array_column)).getItem(0))


def pivot_table(df: DataFrame, index_col: str, pivot_col: str, 
                value_col: str, agg_func: str = "sum") -> DataFrame:
    """Pivot a table (long to wide format)."""
    return df.groupBy(index_col).pivot(pivot_col).agg(expr(f"{agg_func}({value_col})"))


def unpivot_table(df: DataFrame, id_cols: List[str], 
                  value_cols: List[str],
                  variable_col: str = "variable",
                  value_col: str = "value") -> DataFrame:
    """Unpivot a table (wide to long format)."""
    from pyspark.sql.functions import stack
    
    stack_expr = ", ".join([f"'{c}', {c}" for c in value_cols])
    stack_expr = f"stack({len(value_cols)}, {stack_expr}) as ({variable_col}, {value_col})"
    
    return df.select(*id_cols, expr(stack_expr))


def add_surrogate_key(df: DataFrame, key_column: str = "sk") -> DataFrame:
    """Add monotonically increasing surrogate key."""
    return df.withColumn(key_column, monotonically_increasing_id())


def add_row_number(df: DataFrame, partition_by: List[str], 
                   order_by: List[str], 
                   column_name: str = "row_num") -> DataFrame:
    """Add row number within partition."""
    from pyspark.sql.window import Window
    
    window = Window.partitionBy(*partition_by).orderBy(*order_by)
    return df.withColumn(column_name, row_number().over(window))


def deduplicate_latest(df: DataFrame, key_columns: List[str], 
                       timestamp_column: str) -> DataFrame:
    """Keep latest record per key based on timestamp."""
    window = Window.partitionBy(*key_columns).orderBy(desc(timestamp_column))
    return df.withColumn("_rn", row_number().over(window)) \
             .filter(col("_rn") == 1) \
             .drop("_rn")


def fill_nulls(df: DataFrame, fill_values: Dict[str, Any]) -> DataFrame:
    """Fill null values with specified defaults."""
    return df.fillna(fill_values)


def standardize_timestamp(df: DataFrame, column: str, 
                          input_format: Optional[str] = None) -> DataFrame:
    """Standardize timestamp column to UTC."""
    if input_format:
        return df.withColumn(column, to_timestamp(col(column), input_format))
    return df.withColumn(column, to_timestamp(col(column)))


def add_date_parts(df: DataFrame, timestamp_column: str, 
                   prefix: str = "") -> DataFrame:
    """Extract date parts from timestamp column."""
    base = prefix or timestamp_column
    return df \
        .withColumn(f"{base}_year", year(col(timestamp_column))) \
        .withColumn(f"{base}_month", month(col(timestamp_column))) \
        .withColumn(f"{base}_day", dayofmonth(col(timestamp_column))) \
        .withColumn(f"{base}_hour", hour(col(timestamp_column))) \
        .withColumn(f"{base}_day_of_week", dayofweek(col(timestamp_column))) \
        .withColumn(f"{base}_week_of_year", weekofyear(col(timestamp_column)))


def hash_columns(df: DataFrame, columns: List[str], 
                 algorithm: str = "md5", 
                 output_column: str = "row_hash") -> DataFrame:
    """Create hash of specified columns for change detection."""
    concat_expr = concat_ws("||", *[col(c) for c in columns])
    return df.withColumn(output_column, expr(f"{algorithm}({concat_expr})"))


def apply_scd_type2(df: DataFrame, key_columns: List[str],
                    track_columns: List[str],
                    effective_from: str = "effective_from",
                    effective_to: str = "effective_to",
                    is_current: str = "is_current") -> DataFrame:
    """Apply Slowly Changing Dimension Type 2 logic."""
    from pyspark.sql.window import Window
    
    # This is a simplified version - full SCD2 requires merge with target table
    window = Window.partitionBy(*key_columns).orderBy(*[col(c) for c in track_columns])
    
    return df \
        .withColumn("_prev_hash", lag(hash_columns(df, track_columns).col("row_hash")).over(window)) \
        .withColumn("_changed", col("row_hash") != col("_prev_hash")) \
        .withColumn(effective_from, current_timestamp()) \
        .withColumn(effective_to, lit(None).cast(TimestampType())) \
        .withColumn(is_current, lit(True))


def sampling(df: DataFrame, fraction: float, seed: int = 42, 
             with_replacement: bool = False) -> DataFrame:
    """Random sampling of DataFrame."""
    return df.sample(withReplacement=with_replacement, fraction=fraction, seed=seed)


def stratified_sampling(df: DataFrame, stratum_column: str, 
                        fractions: Dict[Any, float], seed: int = 42) -> DataFrame:
    """Stratified sampling by column."""
    return df.sampleBy(stratum_column, fractions, seed)


# Data quality transformations
def remove_outliers_iqr(df: DataFrame, column: str, 
                        multiplier: float = 1.5) -> DataFrame:
    """Remove outliers using IQR method."""
    quantiles = df.approxQuantile(column, [0.25, 0.75], 0.01)
    q1, q3 = quantiles[0], quantiles[1]
    iqr = q3 - q1
    lower_bound = q1 - multiplier * iqr
    upper_bound = q3 + multiplier * iqr
    
    return df.filter((col(column) >= lower_bound) & (col(column) <= upper_bound))


def cap_outliers(df: DataFrame, column: str, 
                 lower_percentile: float = 0.01,
                 upper_percentile: float = 0.99) -> DataFrame:
    """Cap outliers at specified percentiles."""
    lower, upper = df.approxQuantile(column, [lower_percentile, upper_percentile], 0.01)
    return df.withColumn(column, 
        when(col(column) < lower, lower)
        .when(col(column) > upper, upper)
        .otherwise(col(column)))


def normalize_column(df: DataFrame, column: str, 
                     method: str = "minmax",
                     output_column: Optional[str] = None) -> DataFrame:
    """Normalize numeric column."""
    out_col = output_column or f"{column}_normalized"
    
    if method == "minmax":
        stats = df.agg(min(column).alias("min"), max(column).alias("max")).collect()[0]
        min_val, max_val = stats["min"], stats["max"]
        return df.withColumn(out_col, (col(column) - min_val) / (max_val - min_val))
    
    elif method == "zscore":
        stats = df.agg(mean(column).alias("mean"), stddev(column).alias("std")).collect()[0]
        mean_val, std_val = stats["mean"], stats["std"]
        return df.withColumn(out_col, (col(column) - mean_val) / std_val)
    
    return df


def encode_categorical(df: DataFrame, column: str, 
                       method: str = "onehot",
                       output_prefix: Optional[str] = None) -> DataFrame:
    """Encode categorical column."""
    prefix = output_prefix or column
    
    if method == "onehot":
        from pyspark.ml.feature import OneHotEncoder, StringIndexer
        indexer = StringIndexer(inputCol=column, outputCol=f"{prefix}_indexed")
        encoder = OneHotEncoder(inputCol=f"{prefix}_indexed", outputCol=f"{prefix}_encoded")
        return encoder.transform(indexer.fit(df).transform(df))
    
    elif method == "label":
        from pyspark.ml.feature import StringIndexer
        indexer = StringIndexer(inputCol=column, outputCol=f"{prefix}_encoded")
        return indexer.fit(df).transform(df)
    
    return df