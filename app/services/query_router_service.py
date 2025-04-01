#query_router_service.py
import json
import logging
import os
from typing import Dict, List
from llama_index.llms.azure_openai import AzureOpenAI

logger = logging.getLogger(__name__)

class QueryRouter:
    def __init__(self):
        """Initialize QueryRouter with LLM."""
        self.llm = AzureOpenAI(engine='gpt-4o-mini',
            model=('gpt-4o-mini'),
            api_key=os.getenv('AZURE_OPENAI_API_KEY'),
            azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT_MINI'),
            api_version=os.getenv('AZURE_OPENAI_API_VERSION'),
            )
        # self.index_stores = {
        #     "dbm2024budget": "Contains all details about the 2024 budget, including allocations, expenditures, policies, and financial reports.",
        #     "dbm2025budget": "Holds comprehensive information on the 2025 budget, covering planned allocations, proposed expenditures, financial strategies, and policies.",
        #     "dbmrafiles": "Stores Republic Acts (RA) documents from the government, including legal provisions, amendments, and related legislative information.",
        # }
        self.index_stores = {
    # "dbm2024md": "Contains all details about the 2024 budget, including allocations, expenditures, policies, and financial reports.",
    # "dbm2025md": "Holds comprehensive information on the 2025 budget, covering planned allocations, proposed expenditures, financial strategies, and policies.",
    "dbmramd": "Stores Republic Acts (RA) related to government procurement, including RA 9184 and its amendments, implementing rules and regulations (IRR), and other legislative provisions governing procurement processes in the Philippines.",
}


        logger.debug("Initialized QueryRouter with %d index stores", len(self.index_stores))  # Added

    def route_query(self, question: str) -> Dict[str, List[str]]:
        """Route query to appropriate index stores."""
        try:
            logger.debug("Routing question: %s", question)  # Added
            response = self.llm.complete(
                prompt=f"""Given this user question with chat history: {question}
                You are an expert at routing user queries to relevant data sources.
                Please understand the chat history first and rewrite the query by understanding full context then select the most relevant data sources from the following list, please incluse multiple data sources if applicable.
                If query is a greeting , don't include any data source.
                ### Task:
                - Given a user's question, select the most relevant data sources from the following list:
                {self.index_stores}
                - If multiple data sources are relevant, include all applicable ones.
                - If none of the data sources are relevant, return all data sources.
                Return ONLY a JSON object (without any markdown or code blocks) in this format:
                {{
                    "datasources": ["dbm2025budget","rafiles","dbm2024budget"]
                }}""",
                temperature=0.0,
                max_tokens=150
            )
            
            logger.debug("Received LLM response: %s", response.text)  # Added
            # Clean and parse response
            text = response.text.replace("```json\n", "").replace("```", "").replace("'", '"')
            result = json.loads(text)
            logger.debug("Parsed response: %s", result)  # Added
            
            # Validate datasources exist in index_stores
            valid_sources = [
                source for source in result["datasources"]
                if source in self.index_stores
            ]
            logger.info("Validated sources: %s", valid_sources)  # Added
            
            return {"datasources": valid_sources}
            
        except Exception as e:
            logger.error("Error routing query: %s", str(e), exc_info=True)  # Improved
            return {"datasources": list(self.index_stores.keys())}

    def get_index_store(self, datasource: str) -> str:
        """Get the index store name for a datasource."""
        logger.debug("Retrieving index store for: %s", datasource)  # Added
        return self.index_stores.get(datasource)