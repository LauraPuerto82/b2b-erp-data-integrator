from pydantic import BaseModel


class CanonicalCustomer(BaseModel):
    name: str
    tax_id: str
    country: str
    email: str | None = None
