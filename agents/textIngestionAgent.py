import os
from crewai import Agent, Task, Crew
from dotenv import load_dotenv

load_dotenv() 

ingestion_agent = Agent(
    role='Text Ingestion and Standardization Specialist',
    goal='Accept raw, unstructured text input (like emails or messages) and output a clean, '
         'standardized text string ready for entity extraction.',
    backstory='You are the front line of the FinanceFlow system. Your main job is to '
              'handle messy, real-world communication and prepare it so the downstream '
              'agents can reliably extract data. You ensure quality control at the input.',
)

def run_text_ingestion(transaction_text: str,) -> Task:
    """
    Creates the specific task for the Ingestion Agent.
    """
    example_text = """
        Subject: Friday Lunch Hello Derek, I hope that you are doing well. Just giving you a heads-up that I sent the $6 for the burger you got me the other day. Thanks a bunch! I really appreciate it. How is your son doing? He must be getting pretty big now -- can't wait to see him! Talk soon, - Tom 

        From the above raw text, you should return:
        Hello Derek, I sent the $6 for the burger you got me the other day. Talk soon, Tom.
        """


    task = Task(
        description=f"Analyze the following raw text input and output only the sentences mentioning people or a financial amount. "
                    f"Example: {example_text}"
                    f"If there are multiple transactions, output one transaction (including payer(s), payee(s), amount) per line. Include the date of the transaction if mentioned. "
                    f"The final output must be pure text ready for the Entity Extraction Agent. "
                    f"Raw Text Input: {transaction_text}",

        agent=ingestion_agent,
        expected_output="A list of every transaction mentioned in the raw text input.",
    )

    crew = Crew(agents=[ingestion_agent], tasks=[task], verbose=False)
    result = crew.kickoff()

    return result
