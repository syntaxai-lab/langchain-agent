from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from typing import List, Optional
from langchain.agents import create_tool_calling_agent, AgentExecutor
from tools import save_tool, fetch_sec_contract_tool
import json


load_dotenv()


class ClauseAnalysis(BaseModel):
    clause_type: str              # e.g., "Termination", "Indemnification", "Payment Terms"
    original_text: str
    simplified_text: str
    risk_flags: Optional[List[str]]  # e.g., ["vague", "unilateral", "ambiguous"]

class ContractSummary(BaseModel):
    company_name: Optional[str]
    parties: List[str]
    effective_date: Optional[str]
    key_terms: List[str]
    high_risk_clauses: List[ClauseAnalysis]
    simplified_summary: str
    sources: List[str]
    
    
google_llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-001")

# Quick check that its loading properly
# response = google_llm.invoke("hi")
# print(response)

parser = PydanticOutputParser(pydantic_object=ContractSummary)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are a legal research assistant specializing in contracts and SEC filings. 
            Identify and simplify clauses related to termination, indemnity, payment, dispute resolution, and confidentiality.
            Answer the user query by using the available tools when needed.
            Only return the output using this format:\n{format_instructions}
            """,
        ),
        ("placeholder", "{chat_history}"),
        ("human", "{query}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
).partial(format_instructions=parser.get_format_instructions())

tools = [fetch_sec_contract_tool, save_tool]
agent = create_tool_calling_agent(
    llm=google_llm,
    prompt=prompt,
    tools=tools
)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
query = input("What contract or SEC filing would you like to analyze? (e.g., 'Summarize the latest 10-K from Tesla')\n> ")
raw_response = agent_executor.invoke({"query": query})

try:
    # Remove markdown wrapping if present
    raw_output = raw_response["output"]
    if raw_output.startswith("```json"):
        raw_output = raw_output.strip("```json").strip("```").strip()

    structured_response = parser.parse(raw_output)
    print(structured_response)
except Exception as e:
    print("Error parsing response", e, "Raw Response - ", raw_response)

# from tools import fetch_contract_text

# # Directly test what the tool returns
# text = fetch_contract_text("TSLA", "10-K")

# print("=== Preview of fetched SEC text ===")
# print(text[:2000])

# response = google_llm.invoke(f"""Identify and simplify clauses related to termination, indemnity, payment, dispute resolution, and confidentiality.
# Below is an excerpt from a 10-K SEC filing for Tesla:

# {text[:3000]}

# Please extract:
# - Company name
# - Involved parties
# - Effective date (if available)
# - Key terms or financial clauses
# - Any risky or vague legal language

# Respond in this format:
# {parser.get_format_instructions()}
# """)

# print("=== LLM Response ===")
# print(response)
