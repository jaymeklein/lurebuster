from pydantic import BaseModel, EmailStr

class Model(BaseModel):
    first_name: str
    last_name: str
    street: str
    city: str
    state: str
    zipcode: str
    mobile: str
    ccnumb: int
    mmonth: str
    email: EmailStr
    cvvz: int