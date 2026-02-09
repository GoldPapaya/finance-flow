import pyshacl
from crewai.tools import tool
import os
from io import StringIO
from rdflib import Graph
from crewai import Agent, Task, Crew
from dotenv import load_dotenv

load_dotenv() 

SHAPES_FILE_PATH = os.path.join(os.getcwd(), 'finance_shapes.ttl')

@tool("SHACLValidator")
def validate_rdf_graph(rdf_graph_ttl_str: str) -> str:
    """
    Validates an RDF graph (in Turtle string format) against the defined SHACL 
    rules in the finance_shapes.ttl file.
    Returns the validation report (result of pyshacl validation).
    """
    if not os.path.exists(SHAPES_FILE_PATH):
        return f"ERROR: SHACL Shapes file not found at {SHAPES_FILE_PATH}. Validation cannot proceed."

    data_graph = Graph().parse(data=rdf_graph_ttl_str, format='turtle')
    
    try:
        conforms, results_graph, results_text = pyshacl.validate(
            data_graph,
            shacl_graph=SHAPES_FILE_PATH,
            inference='rdfs',
            abort_on_error=False,
            allow_infos=False
        )

        if conforms:
            return "✅ The RDF graph successfully conforms to all defined SHACL constraints."
        else:
            return f"❌ Validation Failed. Violations Found:\n{results_text}"
            
    except Exception as e:
        return f"ERROR during SHACL validation: {e}"

shacl_agent = Agent(
    role='SHACL Data Quality Validator',
    goal='Assess the generated RDF graph against SHACL constraints and report on data quality, flagging any violations.',
    backstory='You are the quality gatekeeper. You ensure the semantic data is structurally sound and meets all required business rules before deployment.',
    verbose=True,
    allow_delegation=False,
    tools=[validate_rdf_graph], 
)

def run_shacl_validation(rdf_graph_ttl_str: str) -> str:
    """Creates and runs the task to validate the RDF graph."""
    task = Task(
        description=(
            "Use the SHACLValidator tool to check the following RDF graph. "
            "Analyze the result from the tool and provide a clear, concise final summary. "
            
            "**CRITICAL INSTRUCTION:** Count the total number of unique transactions referenced in the validation report (e.g., ft:txn-...). "
            "Then, count the number of transactions that had at least one violation (the invalid ones). "
            "Finally, state the total number of valid transactions (Total - Invalid). "
            
            "If violations are found, explicitly list the type of violation (e.g., 'missing ft:payer') and the number of transactions affected."
            f"\n\nRDF Graph to Validate:\n{rdf_graph_ttl_str}"
        ),
        agent=shacl_agent,
        expected_output="A summary stating whether the graph passed validation. If it failed, list the specific rules violated, and state the count of valid and invalid transactions.",
    )
    crew = Crew(agents=[shacl_agent], tasks=[task], verbose=False)
    result = crew.kickoff()
    return result