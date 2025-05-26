from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_openai import ChatOpenAI
# from langchain_anthropic import ChatAnthropic


load_dotenv()

google_llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-001")
# openai_llm = ChatOpenAI(model='gpt-3.5-turbo')
# anthropic_llm = ChatAnthropic(model='claude-sonnet')


# Quick check that its loading properly
response = google_llm.invoke("hi")
print(response)
