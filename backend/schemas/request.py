from pydantic import BaseModel


class ScreeningRequest(BaseModel):
    job_description: str
    top_n: int = 10
