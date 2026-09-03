from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from uuid import UUID, uuid5

from b2b_erp_data_integrator.models.customer import CanonicalCustomer

CUSTOMER_ID_NAMESPACE = UUID("57da2380-82c6-40a6-8e94-a77ee513bdfd")


@dataclass(frozen=True)
class IdentifiedCanonicalCustomer:
    customer_id: UUID
    customer: CanonicalCustomer


def generate_customer_id(customer: CanonicalCustomer) -> UUID:
    identity_key = f"{customer.country}:{customer.tax_id}"

    return uuid5(
        CUSTOMER_ID_NAMESPACE,
        identity_key,
    )


def identify_customer(
    customer: CanonicalCustomer,
) -> IdentifiedCanonicalCustomer:
    return IdentifiedCanonicalCustomer(
        customer_id=generate_customer_id(customer),
        customer=customer,
    )


def deduplicate_customers(
    customers: Iterable[IdentifiedCanonicalCustomer],
) -> Iterator[IdentifiedCanonicalCustomer]:
    seen_ids: set[UUID] = set()

    for customer in customers:
        if customer.customer_id in seen_ids:
            continue

        seen_ids.add(customer.customer_id)
        yield customer
