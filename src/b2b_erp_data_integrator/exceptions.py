class CustomerValidationError(Exception):
    """Raised when customer data fails a supported business validation."""


class IngestionError(Exception):
    """Raised when input data cannot be ingested correctly."""
