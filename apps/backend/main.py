import instructor
from pydantic import BaseModel
from openai import OpenAI


class Person(BaseModel):
    name: str
    age: int
    occupation: str


client = instructor.from_openai(OpenAI(
    api_key="sk-Ejd4Tymd1JoP8AxUW5BHWA",
    base_url="http://0.0.0.0:4000",
))

def main():
    person = client.chat.completions.create(
    model="claude-3.5-sonnet",
    response_model=Person,
    messages=[
        {"role": "user", "content": "Extract: John is a 30-year-old software engineer"}
    ],
)
    print(person)


if __name__ == "__main__":
    main()
