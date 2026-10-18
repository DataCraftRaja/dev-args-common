"""Python code to demonstrate addition of two columns."""

import pandas as pd
import numpy as np


def add_columns_pandas():
    """Add two columns using pandas DataFrame."""
    # Create a sample DataFrame
    df = pd.DataFrame({
        'column_a': [1, 2, 3, 4, 5],
        'column_b': [10, 20, 30, 40, 50]
    })
    
    # Add the two columns
    df['sum'] = df['column_a'] + df['column_b']
    
    print("Pandas DataFrame:")
    print(df)
    print()


def add_columns_numpy():
    """Add two columns using numpy arrays."""
    # Create two numpy arrays
    column_a = np.array([1, 2, 3, 4, 5])
    column_b = np.array([10, 20, 30, 40, 50])
    
    # Add the arrays
    sum_column = column_a + column_b
    
    print("NumPy Arrays:")
    print(f"Column A: {column_a}")
    print(f"Column B: {column_b}")
    print(f"Sum:      {sum_column}")
    print()


def add_columns_lists():
    """Add two columns using Python lists."""
    # Create two lists
    column_a = [1, 2, 3, 4, 5]
    column_b = [10, 20, 30, 40, 50]
    
    # Add the lists element-wise
    sum_column = [a + b for a, b in zip(column_a, column_b)]
    
    print("Python Lists:")
    print(f"Column A: {column_a}")
    print(f"Column B: {column_b}")
    print(f"Sum:      {sum_column}")
    print()


def multiply_columns_pandas():
    """Multiply two columns using pandas DataFrame."""
    # Create a sample DataFrame
    df = pd.DataFrame({
        'column_a': [1, 2, 3, 4, 5],
        'column_b': [10, 20, 30, 40, 50]
    })
    
    # Multiply the two columns
    df['product'] = df['column_a'] * df['column_b']
    
    print("Pandas DataFrame (Multiplication):")
    print(df)
    print()


def multiply_columns_numpy():
    """Multiply two columns using numpy arrays."""
    # Create two numpy arrays
    column_a = np.array([1, 2, 3, 4, 5])
    column_b = np.array([10, 20, 30, 40, 50])
    
    # Multiply the arrays
    product_column = column_a * column_b
    
    print("NumPy Arrays (Multiplication):")
    print(f"Column A: {column_a}")
    print(f"Column B: {column_b}")
    print(f"Product:  {product_column}")
    print()


def multiply_columns_lists():
    """Multiply two columns using Python lists."""
    # Create two lists
    column_a = [1, 2, 3, 4, 5]
    column_b = [10, 20, 30, 40, 50]
    
    # Multiply the lists element-wise
    product_column = [a * b for a, b in zip(column_a, column_b)]
    
    print("Python Lists (Multiplication):")
    print(f"Column A: {column_a}")
    print(f"Column B: {column_b}")
    print(f"Product:  {product_column}")
    print()


if __name__ == "__main__":
    add_columns_pandas()
    add_columns_numpy()
    add_columns_lists()
    
    print("=" * 50)
    print("MULTIPLICATION OPERATIONS")
    print("=" * 50)
    
    multiply_columns_pandas()
    multiply_columns_numpy()
    multiply_columns_lists()