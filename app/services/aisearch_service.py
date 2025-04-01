#aisearch.pyy
import os
import warnings
from dotenv import load_dotenv
import logging
from typing import List, Optional
from llama_index.core import Document
from llama_index.core.readers.base import BaseReader
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType
from azure.search.documents.models import QueryAnswerType
from azure.search.documents.models import QueryCaptionType 
from azure.search.documents.models import QueryDebugMode
from azure.search.documents.models import VectorizableTextQuery
from services.llm_services import LLMService
from services.logging_config import setup_logging  # Import the logging setup

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Load environment variables
load_dotenv(override=True)

# Setup logging
logger=setup_logging()

class AzCognitiveSearchReader(BaseReader):
    """General reader for any Azure Cognitive Search index reader."""

    def __init__(self, service_name: str, search_key: str, index: str) -> None:
        """Initialize Azure cognitive search service using the search key."""
        logger.info("Initializing Azure Search client for index: %s", index)  # Added
        azure_credential = AzureKeyCredential(search_key)

        self.search_client = SearchClient(
            endpoint=f"https://{service_name}.search.windows.net",
            index_name=index,
            credential=azure_credential,
        )

    def search(self, query: str, configuration_name: str) -> List[Document]:
        """
        Perform search on Azure Cognitive Search with the specified parameters.
        """
        try:
            logger.debug("Searching with config '%s': %s", configuration_name, query)  # Added
            vector_query = VectorizableTextQuery(text=query, k_nearest_neighbors=50, fields="text_vector")
            search_result = self.search_client.search(
                search_text=query,
                vector_queries=[vector_query],
                query_type=QueryType.SEMANTIC,
                semantic_configuration_name=configuration_name, 
                query_rewrites="generative|count-3",
                query_language="en",
                debug=QueryDebugMode.Query_REWRITES,
                query_caption=QueryCaptionType.EXTRACTIVE,
                query_answer=QueryAnswerType.EXTRACTIVE,
                select="chunk_id, title, chunk",
                search_fields=["chunk"],
                top=10
            )
            text_query = search_result.get_debug_info().query_rewrites.text.rewrites
            logger.info("Rewritten Queries: %s", text_query)
            documents = []
            for result in search_result:
                documents.append(
                    Document(
                        text=result['chunk'],
                        metadata={
                            "title": result["title"],
                            "score": result["@search.score"],
                        },
                    )
                )
            logger.info("Retrieved %d documents for query: %s", len(documents), query)  # Improved
            return documents
        except Exception as e:
            logger.error("Search failed: %s", str(e), exc_info=True)  # Added
            raise 

# # Function to query using LLM and Azure AI Search context
# def vector_query_with_search(query):
#     # Retrieve relevant documents from Azure AI Search
#     search_results = search_reader.search(query, 
#                                           query_type=QueryType.SEMANTIC,  
#                                           top=30)
    
#     # Combine the content of the retrieved documents, including title and headers
#     context = "\n\n".join([f"Title: {doc.metadata['title']}\nText: {doc.text}" 
#                            for doc in search_results])

#     # Formulate the augmented query by appending the context
#     augmented_query = f"Context: {context}\n\nQuestion: {query}"
    
    
#     # Generate the response using the LLM
#     response = llm.complete(augmented_query)

#     # Log both the LLM response and the references
#     logger.info(f"LLM Response: {response}")

#     # Return the response with references appended
#     final_response = response
#     return final_response


# # Example usage
# if __name__ == "__main__":
#    # Streamlit UI
#     st.title("AI SEARCH")

#     # Function to handle the user query
#     def handle_query():
#         if user_input:
#             with st.spinner('Fetching the response...'):
#                 try:
#                     response = vector_query_with_search(user_input)
#                     st.write(f"**Chatbot Response:** {response}")
#                 except Exception as e:
#                     logger.error(f"Error during query processing: {e}")
#                     st.error("An error occurred. Please try again.")
#         else:
#             st.warning("Please enter a query.")

#     # Create a session state to track the user input
#     if 'user_input' not in st.session_state:
#         st.session_state.user_input = ""

#     # Input from the user, with the "on_change" event tied to the handle_query function
#     user_input = st.text_input("Enter your query:", key='user_input')

#     # Optionally, also have a button for querying
#     if st.button("Ask"):
#         handle_query()

