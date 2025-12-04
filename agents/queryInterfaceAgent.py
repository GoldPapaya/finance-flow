from crewai.tools import tool
from rdflib import Graph
from crewai import Agent, Task, Crew
from dotenv import load_dotenv

load_dotenv()

@tool("SPARQLQueryExecutor")
def execute_sparql_query(rdf_graph_ttl_str: str, sparql_query: str) -> str:
    """
    Executes a SPARQL query against an RDF graph (in Turtle format). 
    
    Returns the results formatted as a list of strings for the LLM to process.
    """
    g = Graph()
    
    try:
        g.parse(data=rdf_graph_ttl_str, format='turtle')
        results = g.query(sparql_query)
        output_lines = []
        vars = [str(v) for v in results.vars]
        for row in results:
            row_data = []
            for var_name in vars:
                val = row[str(var_name)].toPython() if row[str(var_name)] is not None else "None"
                row_data.append(f"{var_name}: {val}")
            
            output_lines.append(", ".join(row_data))
            
        if not output_lines:
            return "Query executed successfully, but no results were found."
            
        return "\n".join(output_lines)
        
    except Exception as e:
        return f"ERROR during SPARQL query execution: {e.__class__.__name__}: {str(e)}"

query_agent = Agent(
    role='SPARQL Query Translator and Executor',
    goal='Answer user questions by translating them into SPARQL queries, executing the query against the RDF graph, and interpreting the results back into natural language.',
    backstory=(
        "You are the knowledge access layer of FinanceFlow. You are highly skilled in SPARQL "
        "and know the FinanceFlow ontology (ft:Transaction, ft:payer, ft:payee, ft:amount, etc.) "
        "intimately. Your primary function is to turn user intent into actionable queries."
    ),
    verbose=True,
    allow_delegation=False,
    tools=[execute_sparql_query], 
)

def run_query_agent(rdf_graph_ttl_str: str, user_question: str) -> str:
    """
    Creates and runs the task for the Query Agent.
    
    Args:
        rdf_graph_ttl_str: The final Turtle graph output from the RDF Construction Agent.
        user_question: The natural language question posed by the user.
    """
    task = Task(
        description=(
            "You have been provided with the following RDF graph (in Turtle format) and a user question. "
            "Your steps are:"
            "1. **Translate** the user question into a valid, precise SPARQL query using the appropriate prefixes (ft:, schema:, foaf:)."
            "2. **Execute** the SPARQLQueryExecutor tool, passing the entire RDF graph string and your generated SPARQL query."
            "3. **Analyze** the structured results returned by the tool."
            "4. **Formulate** a final, clear, and concise answer to the original user question based *only* on the query results."
            
            f"\n\nUser Question: {user_question}"
            f"\n\nRDF Graph:\n{rdf_graph_ttl_str}"
        ),
        agent=query_agent,
        expected_output="A direct, natural language answer to the user's question, based on the executed SPARQL query.",
    )
    crew = Crew(agents=[query_agent], tasks=[task], verbose=False)
    result = crew.kickoff()
    return result