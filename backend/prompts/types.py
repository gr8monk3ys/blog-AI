from typing import Literal, TypedDict

class SystemPrompts(TypedDict):
    title: str
    description: str
    index: str
    body: str

Stack = Literal[
    "title",
    "description",
    "index",
    "body",
]