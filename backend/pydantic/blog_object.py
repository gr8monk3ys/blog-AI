from typing import List
from langchain_core.pydantic_v1 import BaseModel, Field

class Subtopic(BaseModel):
    title: str = Field(description="The title of the subtopic")
    content: str = Field(description="The content of the subtopic")

class Section(BaseModel):
    title: str = Field(description="The title of the section")
    subtopics: List[Subtopic] = Field(description="The subtopics within the section")

class BlogIndex(BaseModel):
    title: str = Field(description="The title of the blog")
    sections: List[Section] = Field(description="The sections of the blog with their subtopics")
