import json
import logging
import os
import re
from llama_index.llms.azure_openai import AzureOpenAI
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

# Define a model for the expected output from the LLM.
class QueryRewriterOutput(BaseModel):
    queries: list[str]

class QueryRewriter:
    def __init__(self):
        """Initialize QueryRewriter with LLM."""
        self.llm = AzureOpenAI(
            engine='gpt-4o-mini',
            model='gpt-4o-mini',
            api_key=os.getenv('AZURE_OPENAI_API_KEY'),
            azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT_MINI'),
            api_version=os.getenv('AZURE_OPENAI_API_VERSION'),
        )
        logger.debug("Initialized QueryRewriter with LLM")

    def fix_json(self, json_str: str) -> str:
        """
        Perform simple cleanup on a JSON string to remove common issues
        such as trailing commas.
        """
        # Remove leading/trailing whitespace
        json_str = json_str.strip()
        # Remove any trailing commas in objects or arrays (e.g., {"queries": ["a", "b",]}).
        json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
        return json_str

    def rewrite_query(self, question: str, num_queries: int, include_original: bool = False) -> list:
        """
        Rewrite the user query to be clear, concise, and context-aware.
        Generates multiple alternative rewrites if requested.

        Args:
            question (str): The original user query, potentially including chat history.
            num_queries (int): The number of alternative queries to generate.
            include_original (bool): If True, include the original query in the returned list.

        Returns:
            list: A list of rewritten queries. If include_original is True, the original query is added.
        """
        try:
            logger.debug("Rewriting query: %s with %d alternative(s)", question, num_queries)
            prompt = f"""You are an expert at query rewriting.
Given the user query along with its chat history:
{question}
Please understand the Query and previous context properly, only then generate alternative rewrites of the query.
Please rewrite the query so that it is clear, concise, and contextually accurate while preserving all the important details.
Please use proper English rules and grammar.
Generate exactly {num_queries} alternative rewrites.
Return ONLY a JSON object in the following format:
{{
  "queries": ["rewritten query 1", "rewritten query 2", ...]
}}
"""
            response = self.llm.complete(
                prompt=prompt,
                temperature=0.0,
                max_tokens=150 * num_queries
            )
            logger.debug("Received LLM response: %s", response.text)
            
            # Clean the response by removing code fences and converting single quotes to double quotes.
            text = response.text.strip().replace("```json", "").replace("```", "").replace("'", '"')
            
            # Use regex to extract the JSON object from the response.
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                # Clean up the JSON string to fix common formatting issues.
                json_str = self.fix_json(json_str)
                
                try:
                    # Use Pydantic's model_validate_json (in Pydantic v2) to load and validate the JSON.
                    output = QueryRewriterOutput.model_validate_json(json_str)
                    queries = output.queries
                    logger.debug("Parsed rewritten queries: %s", queries)
                    
                    # Optionally add the original query to the list.
                    if include_original:
                        queries.insert(0, question)
                    return queries
                except (ValidationError, json.JSONDecodeError) as e:
                    logger.error("Parsing with Pydantic failed: %s", e)
                    return [question]
            else:
                logger.error("Could not extract a valid JSON object from response: %s", text)
                return [question]

        except Exception as e:
            logger.error("Error rewriting query: %s", str(e), exc_info=True)
            # In case of an error, return the original query in a list as a fallback.
            return [question]

# # Usage Example:
# if __name__ == "__main__":
#     logging.basicConfig(level=logging.DEBUG)
    
#     # Initialize the QueryRewriter.
#     query_rewriter = QueryRewriter(llm=None)
    
#     original_query = "Hey, can you tell me about the budget allocations for fisheries for 2024?"
#     # Generate 3 alternative rewritten queries and include the original query.
#     rewritten_queries = query_rewriter.rewrite_query(original_query, num_queries=3, include_original=True)
    
#     for idx, query in enumerate(rewritten_queries, 1):
#         print(f"Rewritten Query {idx}: {query}")
