#main.py
from services.query_router_service import QueryRouter
from services.llm_services import LLMService
import warnings
from dotenv import load_dotenv
from services.aisearch_service import AzCognitiveSearchReader
import logging
import tiktoken
from fastapi import Request
from services.chat_history import SimpleChatStore
from typing import List, Dict
from services.prompt import get_prompt
import os 

from services.logging_config import setup_logging  # Import the setup function

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Load environment variables
load_dotenv(override=True)

# Setup logging
logger=setup_logging()


# Azure AI Search Configuration
ENDPOINT = os.getenv("SEARCH_ENDPOINT")  # Ensure this is set in your .env
SEARCH_API_KEY = os.getenv("SEARCH_API_KEY")  # Ensure this is set in your .env
SEARCH_INDEX = os.getenv("SEARCH_INDEX")  # Ensure this is set in your .env

# Initialize the LLM and embedding model
llm_initializer = LLMService('config.json')
llm = llm_initializer.get_llm()
embed_model = llm_initializer.get_embed_model()

def connect_search_and_router(router: QueryRouter, query: str,full_query: str):
    """Connect router results with search service."""
    try:
        logger.info("Processing query: %s", full_query)  # Added
        route_result = router.route_query(full_query)
        logger.debug("Routing result: %s", route_result)
        
        all_documents = []
        for datasource in route_result["datasources"]:
            logger.info("Searching datasource: %s", datasource)  # Added
            search_reader = AzCognitiveSearchReader(
                service_name=ENDPOINT.split("//")[1].split(".")[0],
                search_key=SEARCH_API_KEY,
                index=datasource,
            )
            documents = search_reader.search(query, configuration_name=datasource+"-semantic-configuration")
            logger.debug("Found %d documents in %s", len(documents), datasource)  # Added
            all_documents.extend(documents)
        
        logger.info("Total documents collected: %d", len(all_documents))  # Added
        return all_documents
        
    except Exception as e:
        logger.error("Connection failed: %s", str(e), exc_info=True)  # Improved
        raise


# Initialize router with your existing LLM
router = QueryRouter()


def vector_query_with_search(query:str,req: Request,user_id: str = "user-1"):
    try:
        
        logger.debug("Starting vector query processing") 
        chat_store = req.app.state.chat_store
        MAX_HISTORY_TOKENS = 2000
        chat_store.user_chats[user_id] = chat_store.truncate_chat_history(chat_store.user_chats.get(user_id, []), MAX_HISTORY_TOKENS)
        chat_history = chat_store.get_chat_history(user_id)
        if chat_history:
            full_query = f"{chat_history}\n{query}"
        else:
            full_query = query
        search_results = connect_search_and_router(router,query,full_query=full_query)
        logger.debug("Building context from %d documents", len(search_results))  
        
        context = "\n\n".join([f"Title: {doc.metadata['title']}\nText: {doc.text}" 
                            for doc in search_results])
        
        system_prompt=get_prompt()
        
        
        if chat_history:
            augmented_query = f"Previous Chats:\n{chat_history}\n\nContext: {context}\n\nQuestion: {query}\n\ninstructions:{system_prompt}"
        else:
            augmented_query = f"Context: {context}\n\nQuestion: {query}\n\ninstructions:{system_prompt}"
        
        # augmented_query = f"Context: {context}\n\nquery: {query}"
        
        logger.debug("Augmented query length: %d characters", len(augmented_query)) 
        
        logger.debug("Loading encoding model")
        encoding = tiktoken.encoding_for_model("gpt-4o-mini")
        token_list = encoding.encode(augmented_query)
        num_tokens = len(token_list)
        logger.debug(f"Total tokens for the prompt: {num_tokens}") 
    
        response = llm.complete(augmented_query)
        logger.info("LLM response generated successfully")  
        logger.debug("Full LLM response: %s", response.text)
        llm_response_text = response.text.strip() 
        chat_store.add_message(user_id, query, llm_response_text)
        logger.info("Message after adding: %s", chat_store.user_chats)
        return response.text
    except Exception as e:
        logger.error("Vector query failed: %s", str(e), exc_info=True)  
        raise

