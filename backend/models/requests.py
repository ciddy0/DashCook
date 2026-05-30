from pydantic import BaseModel, HttpUrl


class ExtractRequest(BaseModel):
    url: HttpUrl
