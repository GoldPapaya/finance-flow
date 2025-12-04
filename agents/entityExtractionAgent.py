from crewai import Agent, Task, Crew
from dotenv import load_dotenv

load_dotenv() 

extraction_agent = Agent(
    role="Valid Sentence Extractor",
    goal="Extract entities from ingested text.",
    backstory=(
        "You analyze text and extract entities."
        "You express the extracted entities in a JSON."
    )
)

def run_entity_extraction(text):
    task = Task(
        description=(
            "Analyze the clean transaction text below to identify the **Payer** and **Payee** "
            "and normalize the financial details. "
            
            # --- RULE 1: STRICT OUTPUT FORMAT ---
            "Your final output MUST be a **JSON list of dictionaries**, where each dictionary represents "
            "a single distinct transaction. Do not include any text outside the JSON block. "
            "The dictionaries must contain the following keys: **payer_name**, **payee_name**, "
            "**normalized_amount** (as a decimal number), **currency** (e.g., USD), and **normalized_date** (in YYYY-MM-DD format). "
            "Infer the roles (Payer/Payee) based on the verbs (sent, paid, received, owes). "
            "Here are some examples of good output: [{'payer_name': 'Rob', 'payee_name': 'Scott', 'normalized_amount': '', 'currency': '', 'normalized_date': '2025-11-21'}, {'payer_name': '', 'payee_name': 'Tom', 'normalized_amount': '12.00', 'currency': 'USD', 'normalized_date': ''}]. "
            "Each property goes in a seperate line."

            # --- RULE 2: PRONOUN HANDLING ---
            "**STRICT PAYER/PAYEE RULE:** The names must be proper nouns (e.g., 'Sarah', 'Lucas'). "
            "If the payer or payee is only identifiable by a pronoun (e.g., 'I', 'me', 'we', 'they', 'you'), "
            "you MUST set the corresponding field (**payer_name** or **payee_name**) to an **empty string** (''). "
            "DO NOT output pronouns."

            # --- RULE 3: AMBIGUITY HANDLING & DATE FIX ---
            "**STRICT AMBIGUITY RULE:** If *any* field (payer, payee, amount, date) cannot be determined "
            "with **absolute certainty** as a named entity or normalized value, you MUST set its value "
            "to an **empty string** (''). "
            "Specifically for the date: If it contains ambiguous/relative terms like 'yesterday', 'last month', "
            "or 'a while ago' and no specific date is present, set **normalized_date** to ''. "
            "If a specific date (like '11/21/2025') is present, you MUST use the YYYY-MM-DD format."

            # --- RULE 4: PRONOUN-TO-NAME RESOLUTION ---
            "**STRICT PAYER/PAYEE RULE:** "
            "1. **EXPLICIT NAMES COME FIRST:** You **MUST** extract all proper names (e.g., 'Becky', 'Joseph', 'Jacob') "
            "that are explicitly mentioned as Payer or Payee in the current transaction statement. If multiple names are payers, list them separated by commas."
            "2. **PRONOUNS ARE SECONDARY:** If the role is identified by a pronoun ('I', 'me', 'we', 'you', etc.), you **MUST** follow this hierarchy:"
            "    a. If a name can be logically resolved within the **SAME STATEMENT** (e.g., appended signer), use that name."
            "    b. If names were already extracted in step 1 (e.g., 'Becky and I'), **IGNORE THE PRONOUN ('I')** and use only the explicit names."
            "    c. If the role is *only* a pronoun (e.g., 'I just gave you'), and it cannot be resolved by a name in the same statement, set the field to an **empty string** (''). "
            
            f"Text to analyze:\n{text}"
        ),
        agent=extraction_agent,
        expected_output="A JSON list of dictionaries structured like: {'payer_name': '', 'payee_name': '', 'normalized_amount': '', 'currency': '', 'normalized_date': ''}]. Each property goes on a seperate line.",
    )
    crew = Crew(agents=[extraction_agent], tasks=[task], verbose=False)
    result = crew.kickoff()

    return result
