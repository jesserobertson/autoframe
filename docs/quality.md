# Quality Assessment

AutoFrame provides built-in data quality assessment capabilities to help identify and handle data quality issues automatically during dataframe creation.

> **Note**: Quality assessment features are planned for future releases. This documentation describes the intended functionality.

## Overview

Data quality assessment in AutoFrame focuses on:

- **Completeness**: Missing values and null percentages
- **Consistency**: Data type consistency and format validation
- **Accuracy**: Outlier detection and range validation
- **Uniqueness**: Duplicate detection and uniqueness constraints
- **Timeliness**: Date validation and freshness checks

## Basic Quality Assessment

### Automatic Quality Checks

Quality assessment runs automatically when enabled:

```python
from autoframe import mongodb_to_dataframe
from autoframe.config import get_config

# Enable quality assessment
config = get_config()
config.set("quality", "enable_by_default", True)
config.set("quality", "quality_threshold", 0.8)

# Quality assessment runs automatically
result = mongodb_to_dataframe(
    "mongodb://localhost:27017",
    "ecommerce",
    "orders"
)

if result.is_ok():
    df = result.unwrap()
    # Quality metrics are attached as metadata
    quality_info = getattr(df, '_autoframe_quality', {})
    print(f"Quality score: {quality_info.get('overall_score', 'N/A')}")
```

### Manual Quality Assessment

```python
from autoframe.quality import assess_quality

# Assess quality of existing dataframe
quality_result = assess_quality(df)

if quality_result.is_ok():
    quality_report = quality_result.unwrap()
    print(f"Overall quality score: {quality_report.overall_score}")
    print(f"Missing data percentage: {quality_report.missing_percentage}")
    print(f"Duplicate rows: {quality_report.duplicate_count}")
```

## Quality Metrics

### Completeness Metrics

```python
from autoframe.quality import completeness_check

# Check for missing values
completeness_result = completeness_check(df)

if completeness_result.is_ok():
    completeness = completeness_result.unwrap()
    
    print(f"Overall completeness: {completeness.overall_percentage}")
    print("Per-column completeness:")
    for column, percentage in completeness.column_percentages.items():
        print(f"  {column}: {percentage:.1%}")
```

### Consistency Metrics

```python
from autoframe.quality import consistency_check

# Check data type consistency
consistency_result = consistency_check(df)

if consistency_result.is_ok():
    consistency = consistency_result.unwrap()
    
    print(f"Type consistency: {consistency.type_consistency}")
    for column, issues in consistency.type_issues.items():
        if issues:
            print(f"  {column}: {issues}")
```

### Uniqueness Metrics

```python
from autoframe.quality import uniqueness_check

# Check for duplicates
uniqueness_result = uniqueness_check(df, key_columns=["id", "email"])

if uniqueness_result.is_ok():
    uniqueness = uniqueness_result.unwrap()
    
    print(f"Duplicate rows: {uniqueness.duplicate_count}")
    print(f"Uniqueness score: {uniqueness.uniqueness_score}")
    
    if uniqueness.duplicate_rows:
        print("Sample duplicates:")
        print(uniqueness.duplicate_rows.head())
```

## Quality Rules and Validation

### Schema Validation

```python
from autoframe.quality import SchemaValidator

# Define expected schema
schema_rules = {
    "id": {"type": "int", "required": True, "unique": True},
    "email": {"type": "string", "required": True, "pattern": r"^[^@]+@[^@]+\.[^@]+$"},
    "age": {"type": "int", "min": 0, "max": 150},
    "salary": {"type": "float", "min": 0},
    "created_at": {"type": "datetime", "required": True}
}

validator = SchemaValidator(schema_rules)
validation_result = validator.validate(df)

if validation_result.is_ok():
    report = validation_result.unwrap()
    if report.is_valid:
        print("Schema validation passed")
    else:
        print("Schema validation failed:")
        for error in report.errors:
            print(f"  {error}")
```

### Business Rules

```python
from autoframe.quality import BusinessRuleValidator

# Define business rules
rules = [
    {
        "name": "positive_revenue",
        "condition": lambda row: row["revenue"] > 0,
        "message": "Revenue must be positive"
    },
    {
        "name": "valid_order_status", 
        "condition": lambda row: row["status"] in ["pending", "completed", "cancelled"],
        "message": "Invalid order status"
    },
    {
        "name": "reasonable_quantity",
        "condition": lambda row: 0 < row["quantity"] <= 1000,
        "message": "Quantity must be between 1 and 1000"
    }
]

validator = BusinessRuleValidator(rules)
validation_result = validator.validate(df)

if validation_result.is_ok():
    report = validation_result.unwrap()
    print(f"Rules passed: {report.passed_count}/{report.total_rules}")
    
    for failure in report.failures:
        print(f"Rule '{failure.rule_name}' failed on {failure.row_count} rows")
```

## Outlier Detection

### Statistical Outliers

```python
from autoframe.quality import detect_outliers

# Detect statistical outliers
outliers_result = detect_outliers(
    df, 
    columns=["price", "quantity", "rating"],
    method="iqr",  # or "zscore", "isolation_forest"
    threshold=1.5
)

if outliers_result.is_ok():
    outliers = outliers_result.unwrap()
    
    print(f"Found {len(outliers.outlier_indices)} outlier rows")
    print("Outlier summary by column:")
    for column, count in outliers.column_outlier_counts.items():
        print(f"  {column}: {count} outliers")
    
    # Get outlier rows
    outlier_rows = df.iloc[outliers.outlier_indices]
```

### Domain-Specific Outliers

```python
from autoframe.quality import DomainOutlierDetector

# Define domain-specific outlier rules
detector = DomainOutlierDetector({
    "age": {"min": 0, "max": 120},
    "price": {"min": 0, "max": 10000},
    "rating": {"min": 1, "max": 5}
})

outliers_result = detector.detect(df)

if outliers_result.is_ok():
    outliers = outliers_result.unwrap()
    print(f"Domain outliers: {len(outliers.outlier_indices)}")
```

## Quality-Driven Processing

### Conditional Processing

```python
from autoframe.quality import quality_gate

def process_high_quality_data(df):
    """Process data only if quality is sufficient."""
    
    quality_result = assess_quality(df)
    if quality_result.is_err():
        return quality_result
    
    quality_report = quality_result.unwrap()
    
    # Quality gate
    if quality_report.overall_score < 0.8:
        return Err(f"Data quality too low: {quality_report.overall_score}")
    
    # Proceed with processing
    processed_df = df.dropna().drop_duplicates()
    return Ok(processed_df)

# Usage in pipeline
result = (
    mongodb_to_dataframe("mongodb://localhost:27017", "db", "collection")
    .then(process_high_quality_data)
)
```

### Automatic Data Cleaning

```python
from autoframe.quality import auto_clean

# Automatic cleaning based on quality assessment
clean_result = auto_clean(
    df,
    remove_duplicates=True,
    handle_missing="interpolate",  # or "drop", "fill_mean", etc.
    remove_outliers=True,
    outlier_method="iqr"
)

if clean_result.is_ok():
    cleaned_df = clean_result.unwrap()
    print(f"Cleaned data: {len(df)} -> {len(cleaned_df)} rows")
```

## Quality Reporting

### Comprehensive Reports

```python
from autoframe.quality import generate_quality_report

# Generate detailed quality report
report_result = generate_quality_report(
    df,
    include_plots=True,
    export_format="html"  # or "json", "pdf"
)

if report_result.is_ok():
    report = report_result.unwrap()
    
    # Save report
    with open("quality_report.html", "w") as f:
        f.write(report.html_content)
    
    print(f"Quality report saved: {report.summary}")
```

### Quality Monitoring

```python
from autoframe.quality import QualityMonitor

# Monitor quality over time
monitor = QualityMonitor()

# Record quality metrics
monitor.record_quality(
    dataset_name="user_profiles",
    timestamp="2024-01-01T10:00:00",
    quality_score=0.85,
    metrics={
        "completeness": 0.95,
        "consistency": 0.80,
        "uniqueness": 0.90
    }
)

# Get quality trends
trends = monitor.get_trends("user_profiles", days=30)
```

## Configuration

### Quality Settings

```python
from autoframe.config import get_config

config = get_config()

# Quality assessment settings
config.set("quality", "enable_by_default", True)
config.set("quality", "quality_threshold", 0.8)
config.set("quality", "max_null_percentage", 0.1)
config.set("quality", "enable_duplicate_detection", True)
config.set("quality", "enable_outlier_detection", False)

# Outlier detection settings
config.set("quality", "outlier_method", "iqr")
config.set("quality", "outlier_threshold", 1.5)
```

### Environment Variables

```bash
export AUTOFRAME_QUALITY_THRESHOLD=0.9
export AUTOFRAME_MAX_NULL_PERCENTAGE=0.05
export AUTOFRAME_ENABLE_OUTLIER_DETECTION=true
```

## Integration with Pipelines

### Pipeline Quality Gates

```python
from autoframe import create_pipeline
from autoframe.quality import quality_gate

result = (
    create_pipeline(data_source)
    .filter(lambda doc: doc["active"])
    .to_dataframe()
    .apply_schema(schema)
    .then(quality_gate(min_score=0.8))  # Quality gate
    .execute()
)
```

### Quality-Aware Transformations

```python
def quality_aware_processing(df):
    """Adapt processing based on data quality."""
    
    quality_result = assess_quality(df)
    if quality_result.is_err():
        return Err("Quality assessment failed")
    
    quality = quality_result.unwrap()
    
    if quality.missing_percentage > 0.1:
        # High missing data - use conservative approach
        df = df.dropna()
    else:
        # Low missing data - can use interpolation
        df = df.fillna(method="interpolate")
    
    if quality.duplicate_count > 0:
        df = df.drop_duplicates()
    
    return Ok(df)
```

This quality assessment framework ensures that data quality issues are identified early and handled appropriately, leading to more reliable data processing pipelines.