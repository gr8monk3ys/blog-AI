from typing import List
from langchain_core.pydantic_v1 import BaseModel, Field

class Topic(BaseModel):
    title: str = Field(description="The title of the topic")
    content: str = Field(description="The content of the topic")

class Lesson(BaseModel):
    title: str = Field(description="The title of the lesson")
    topics: List[Topic] = Field(description="The topics covered in the lesson")

class Module(BaseModel):
    title: str = Field(description="The title of the module")
    lessons: List[Lesson] = Field(description="The lessons within the module")

class Course(BaseModel):
    title: str = Field(description="The title of the course")
    description: str = Field(description="A brief description of the course")
    modules: List[Module] = Field(description="The modules of the course")