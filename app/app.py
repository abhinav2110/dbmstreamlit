import streamlit as st
from routes.chatengine import vector_query_with_search
from services.chat_history import SimpleChatStore

# Define a dummy app state that holds the chat store.
class DummyAppState:
    def __init__(self):
        self.chat_store = SimpleChatStore()

# Define a dummy app that has a state attribute.
class DummyApp:
    def __init__(self):
        self.state = DummyAppState()

# Define a dummy request that contains the dummy app.
class DummyRequest:
    def __init__(self):
        self.app = DummyApp()

# Create a global dummy request object.
dummy_request = DummyRequest()

# Initialize session state to store chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# App title and layout
st.title("DBM Chatbot")

# Main chat interface container
chat_container = st.container()

# Sidebar for chat history (scrollable)
st.sidebar.title("Chat History")
with st.sidebar:
    chat_history = st.empty()  # Placeholder for displaying chat history
    if st.session_state.chat_history:
        for chat in st.session_state.chat_history:
            st.write(f"**You:** {chat['user_query']}")
            st.write(f"**Bot:** {chat['response']}")

# Input section for user query
user_query = st.text_input("Enter your query:", key="user_query_input")

# Send query and process the response when button is clicked
if st.button("Send Query"):
    if user_query:
        try:
            st.write("Processing query...")
            # Call the vector_query_with_search function using the dummy request.
            response = vector_query_with_search(user_query, dummy_request, user_id="test-user")
            
            # Add the query and response to the chat history
            st.session_state.chat_history.append({
                'user_query': user_query,
                'response': response
            })

            # Update the chat history display
            chat_history.empty()
            with st.sidebar:
                for chat in st.session_state.chat_history:
                    st.write(f"**You:** {chat['user_query']}")
                    st.write(f"**Bot:** {chat['response']}")

            # Display the response in the main container
            with chat_container:
                st.subheader("LLM Response")
                st.write(response)
        
        except Exception as e:
            st.error(f"Error processing query: {e}")

# Option to clear chat history
if st.sidebar.button("Clear Chat History"):
    st.session_state.chat_history = []
    st.sidebar.write("Chat history cleared.")
