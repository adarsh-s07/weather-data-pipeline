# Weather Data Pipeline

A small Python pipeline that requests a one-day forecast for Bengaluru from WeatherAPI and stores the response as JSON in an S3-compatible object store. A separate Snowpark script currently only opens a Snowflake session; it does not yet load the stored data.

See the [project design document](docs/design.md) for the architecture, configuration, runtime flow, current limitations, and recommended next steps.
