from pydantic import BaseModel
from typing import List


class ScreeningRequest(BaseModel):
    job_description: str
    top_n: int = 10
