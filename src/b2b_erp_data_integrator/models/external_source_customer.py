from pydantic import BaseModel

from b2b_erp_data_integrator.models.customer import CanonicalCustomer


class ExternalSourceCustomer(BaseModel):
    source_system: str
    external_id: str
    customer: CanonicalCustomer
