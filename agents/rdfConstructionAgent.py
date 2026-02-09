import json
import uuid
from rdflib import Graph, Literal, Namespace, URIRef, XSD
from rdflib.namespace import RDF, FOAF
from crewai import Agent, Task, Crew
from crewai.tools import tool
from dotenv import load_dotenv

load_dotenv()

FT = Namespace("http://financeflow.example/ontology#")
SCHEMA = Namespace("http://schema.org/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")

@tool("RDFTripleBuilder")
def build_rdf_triples(json_data_str: str) -> str:
    """
    A specialized tool that takes a standardized JSON list of transactions and 
    converts it into a valid RDF graph in Turtle format (.ttl) using rdflib. 
    It handles multiple payers/payees separated by commas.
    """
    g = Graph()
    g.bind("ft", FT)
    g.bind("schema", SCHEMA)
    g.bind("foaf", FOAF)
    
    try:
        cleaned_str = json_data_str.strip().strip('```json').strip('```')
        transactions = json.loads(cleaned_str)
    except json.JSONDecodeError as e:
        return f"JSON PARSING ERROR: {e}. Input was: {json_data_str}"
        
    def create_resource_uri(prefix, name):
        clean_name = name.replace(' ', '_').replace('.', '').lower()
        return URIRef(FT[f"{prefix}-{clean_name}-{uuid.uuid4().hex[:6]}"])
        
    for t_data in transactions:
        transaction_uri = URIRef(FT[f"txn-{uuid.uuid4().hex[:8]}"])
        g.add((transaction_uri, RDF.type, FT.Transaction))
        
        payer_names = t_data.get('payer_name', '').strip()
        payee_names = t_data.get('payee_name', '').strip()
        
        if payer_names:
            names = [n.strip() for n in payer_names.split(',') if n.strip()]
            for name in names:
                payer_uri = create_resource_uri("person", name)
                g.add((payer_uri, RDF.type, FT.Person))
                g.add((payer_uri, FOAF.name, Literal(name, datatype=XSD.string)))
                g.add((transaction_uri, FT.payer, payer_uri))
                
        if payee_names:
            names = [n.strip() for n in payee_names.split(',') if n.strip()]
            for name in names:
                payee_uri = create_resource_uri("person", name)
                g.add((payee_uri, RDF.type, FT.Person))
                g.add((payee_uri, FOAF.name, Literal(name, datatype=XSD.string)))
                g.add((transaction_uri, FT.payee, payee_uri))
        
        amount_val = t_data.get('normalized_amount', '')
        currency_code = t_data.get('currency', '').strip()
        
        if amount_val and currency_code:
            try:
                amount_uri = URIRef(FT[f"amount-{uuid.uuid4().hex[:6]}"])
                g.add((amount_uri, RDF.type, SCHEMA.MonetaryAmount))
                g.add((amount_uri, SCHEMA.value, Literal(float(amount_val), datatype=XSD.decimal)))
                g.add((amount_uri, SCHEMA.currency, Literal(currency_code, datatype=XSD.string)))
                g.add((transaction_uri, FT.amount, amount_uri))
            except ValueError:
                 pass 
            
        date_str = str(t_data.get('normalized_date', '')).strip()
        if date_str:
            g.add((transaction_uri, FT.transactionDate, Literal(date_str, datatype=XSD.date)))
            
    return g.serialize(format='turtle')

rdf_agent = Agent(
    role='RDF Graph Construction Specialist',
    goal='Convert structured transaction data (JSON) into verifiable RDF triples adhering to the FinanceFlow ontology.',
    backstory='You ensure every extracted fact is accurately converted into a machine-readable semantic triple using the RDFTripleBuilder tool.',
    verbose=True,
    allow_delegation=False,
    tools=[build_rdf_triples],
)

def run_rdf_construction(structured_json_str: str) -> str:
    """Creates and runs the task to build RDF triples."""
    task = Task(
        description=(
            "Use the RDFTripleBuilder tool to process the following structured JSON data. "
            "Your output MUST be the complete, valid RDF graph in Turtle format (TTL). "
            "Do not include any other text or explanation."
            f"\n\nJSON Input:\n{structured_json_str}"
        ),
        agent=rdf_agent,
        expected_output="A block of text containing the valid RDF graph in Turtle (.ttl) format.",
    )
    crew = Crew(agents=[rdf_agent], tasks=[task], verbose=False)
    result = crew.kickoff()
    return result