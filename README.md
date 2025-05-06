# Sybase Stored Procedure Converter

This Python script uses GEMINI's GPT model to convert Sybase stored procedure code into a structured requirement document and target state code. It provides a simple function that formats a prompt and sends it to the GEMINI's API to generate a well-organized response.

## 🚀 Features

Converts Sybase stored procedure details into:

- Requirement Document (10 key sections)
- Target State Code

Uses Gemini's `gemini-2.0-flash` model.

Returns formatted response text suitable for saving or further processing.

## 🛠 Prerequisites

- **Python 3.7+**
- **A free active GEMINI API key**
- **pip install requirements**

## 📦 Installation

Create and activate a virtual environment:

```bash
python -m venv venv_name
source venv_name/bin/activate  # On Windows: venv_name\Scripts\activate
``````

Install required package:
```bash
pip install reportlab==4.4.0
pip install fpdf==1.7.2
pip install requests==2.32.3
pip install openai==0.28.0
``````
## 🧠 Usage
Replace the placeholders in config.py in the script:

- api_key = '********************************************' with your actual api key
- target_state = "java spring boot" with the actual conversion type that you want
- file_path = "sybase_proc" with the actual folder where your stored procedures are kept


### Happy Coding...
