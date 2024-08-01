from typing import List, Dict
from langchain_core.pydantic_v1 import BaseModel, Field

class Chapter(BaseModel):
    ChapterNumber: str = Field(description="The chapter number")
    Title: str = Field(description="The title of the chapter")
    Topics: List[str] = Field(description="The topics covered in the chapter")

class Book(BaseModel):
    Title: str = Field(description="The title of the book")
    Chapters: List[Chapter] = Field(description="The chapters of the book")