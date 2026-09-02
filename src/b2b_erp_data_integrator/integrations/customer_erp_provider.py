from collections.abc import Callable
from dataclasses import dataclass

from b2b_erp_data_integrator.models.external_source_customer import (
    ExternalSourceCustomer,
)


@dataclass(frozen=True)
class CustomerERPProvider:
    source_system: str
    field_mapping: dict[str, str]
    mapper: Callable[[dict], ExternalSourceCustomer]
