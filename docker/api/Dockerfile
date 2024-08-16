# Python image
FROM python:3.7

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY ./install/requirements.txt .

# Install the dependencies
RUN pip install -r requirements.txt

# Copy the source code
COPY . .

# Expose the port
EXPOSE 8000

# Run the FastAPI app
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]