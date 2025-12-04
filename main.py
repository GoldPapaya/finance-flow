from agents.textIngestionAgent import run_text_ingestion
from agents.entityExtractionAgent import run_entity_extraction
from agents.rdfConstructionAgent import run_rdf_construction
from agents.validationAgent import run_shacl_validation
from agents.queryInterfaceAgent import run_query_agent

def call_ingestion_agent():
    with open('input.txt', 'r', encoding='utf-8') as f:
        raw_inputs_list = [line.strip() for line in f if line.strip()]

    all_clean_transactions = []
    print(f"--- 1. INGESTION STAGE: Processing {len(raw_inputs_list)} raw inputs ---")
    for i, raw_input in enumerate(raw_inputs_list):
        # run_text_ingestion is called once per raw input line
        clean_output = run_text_ingestion(raw_input)
        all_clean_transactions.append(str(clean_output))
        print(f"✅ Line {i+1} Ingested. Clean output added.")

    combined_input_string = "\n".join(all_clean_transactions)
    print("\n--- Consolidated Clean Input ---\n" + combined_input_string)
    return combined_input_string

def call_extraction_agent(combined_input_string):
    print("\n--- 2. EXTRACTION STAGE: Running Entity Extraction Agent ---")
    final_extraction_output_json = run_entity_extraction(combined_input_string)
    print("✅ Extraction Complete. JSON Output:")
    print(final_extraction_output_json)
    return final_extraction_output_json

def call_rdf_agent(final_extraction_output_json):
    print("\n--- 3. RDF CONSTRUCTION STAGE: Running RDF Construction Agent ---")
    run_rdf_construction(final_extraction_output_json)
    print("✅ RDF Construction Complete. TTL Graph:")

def call_validation_agent(rdf_construction_output):
    print("\n--- 4. SHACL VALIDATION STAGE: Running SHACL Validation Agent ---")
    validation_report = run_shacl_validation(rdf_construction_output)
    print("\n--- FINAL VALIDATION REPORT ---")
    print(validation_report)

def call_query_agent(rdf_construction_output, question):
    result = run_query_agent(rdf_construction_output, question)
    print(result)

if __name__ == '__main__':
    combined_input_string = call_ingestion_agent()
    final_extraction_output_json = call_extraction_agent(combined_input_string)
    call_extraction_agent(final_extraction_output_json)

    rdf_construction_output = ""
    with open("rdf_output.ttl", "r") as f:
        rdf_construction_output = f.read()

    call_validation_agent(rdf_construction_output)

    user_question = "What is the count of all transactions with amounts over $10?"

    call_query_agent(rdf_construction_output, user_question)
