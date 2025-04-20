FROM python:3.11-slim

# working directory
WORKDIR /app

# app files
COPY . .

# Install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Streamlit port
EXPOSE 8501

# Run the app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
