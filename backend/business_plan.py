from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

def generate_section(prompt, template):
    llm = OpenAI(model_name="gpt-4o", temperature=0.7)
    section_template = PromptTemplate(input_variables=["prompt"], template=template)
    section_chain = LLMChain(llm=llm, prompt=section_template)
    return section_chain.run({"prompt": prompt})

def generate_executive_summary(prompt):
    template = """
    Generate an executive summary for a business plan with the following details:
    {prompt}
    """
    return generate_section(prompt, template)

def generate_company_description(prompt):
    template = """
    Generate a company description for a business plan with the following details:
    {prompt}
    """
    return generate_section(prompt, template)

def generate_products_and_services(prompt):
    template = """
    Generate a products and services section for a business plan with the following details:
    {prompt}
    """
    return generate_section(prompt, template)

def generate_market_analysis(prompt):
    template = """
    Generate a market analysis for a business plan with the following details:
    {prompt}
    """
    return generate_section(prompt, template)

def generate_marketing_and_sales(prompt):
    template = """
    Generate a marketing and sales strategy for a business plan with the following details:
    {prompt}
    """
    return generate_section(prompt, template)

def generate_operations_plan(prompt):
    template = """
    Generate an operations plan for a business plan with the following details:
    {prompt}
    """
    return generate_section(prompt, template)

def generate_management_and_organization(prompt):
    template = """
    Generate a management and organization plan for a business plan with the following details:
    {prompt}
    """
    return generate_section(prompt, template)

def generate_financial_plan(prompt):
    template = """
    Generate a financial plan for a business plan with the following details:
    {prompt}
    """
    return generate_section(prompt, template)

def generate_appendix(prompt):
    template = """
    Generate an appendix for a business plan with the following details:
    {prompt}
    """
    return generate_section(prompt, template)
