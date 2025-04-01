import logging
import os

# Ensure logs directory exists
if not os.path.exists("logs"):
    os.makedirs("logs")

# Log file path
log_file_path = os.path.join("logs", "app_logs.log")

# Configure the logger
def setup_logging():
    
    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)

        # Create file handler
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        # Create stream handler (for console output)
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
        file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)

        # Add handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger
# Ensure logs directory exists
if not os.path.exists("logs"):
    os.makedirs("logs")

# Configure logging
log_file_path = os.path.join("logs", "app_logs.log")
logger = logging.getLogger(__name__)

if not logger.hasHandlers():  # Prevent duplicate handlers in Streamlit
    logger.setLevel(logging.DEBUG)
    
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    stream_handler = logging.StreamHandler()
    
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)