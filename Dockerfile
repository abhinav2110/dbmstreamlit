# Use the official Python image as a parent image
FROM python:3.10

# Set the working directory
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy all files to the container
COPY . .

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8000", "--server.address=0.0.0.0"]
