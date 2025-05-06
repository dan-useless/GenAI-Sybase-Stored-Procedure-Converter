import logging
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import re
from datetime import datetime
from fpdf import FPDF
import requests
import datetime
import config
import os
import json

def reading_and_processing_file(file_path, processing_type):
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    with open(file_path, 'r') as file:
        content = file.readlines()

    processing_type = processing_type.upper()

    if processing_type in ['SYBASE']:
        start_keywords = [
            'CREATE PROCEDURE', 
            'CREATE OR REPLACE PROCEDURE', 
            'CREATE TEMPORARY PROCEDURE', 
            'REPLACE PROCEDURE', 
            'CREATE FUNCTION', 
            'CREATE OR REPLACE FUNCTION', 
            'CREATE TEMPORARY FUNCTION', 
            'REPLACE FUNCTION'
        ]
        end_keyword = 'END'
        begin_keyword = 'BEGIN'
    else:
        logging.error(f"Unsupported processing type: {processing_type}")
        raise ValueError(f"Unsupported processing type: {processing_type}")

    processed_chunks = []  # List to store the final chunks of stored procedures/functions
    in_sp = False          # Flag to indicate whether we're inside a stored procedure/function
    sp_chunk = []          # Temporary list to accumulate lines of the current stored procedure/function
    nesting_level = 0      # Counter to handle nested BEGIN-END blocks

    for line in content:
        upper_line = line.upper().strip()
        
        if not in_sp:
            # Check if the current line contains any of the start keywords
            if any(keyword in upper_line for keyword in start_keywords):
                if sp_chunk:
                    # If already inside a stored procedure/function, save the previous one
                    processed_chunks.append(''.join(sp_chunk))
                    sp_chunk = []
                in_sp = True
                nesting_level = 0
                logging.info(f"Stored procedure/function found: {line.strip()}")
        
        if in_sp:
            # Accumulate the lines of the current stored procedure/function
            sp_chunk.append(line)

            # Adjust nesting level for BEGIN and END keywords
            if begin_keyword in upper_line:
                nesting_level += 1
            if end_keyword in upper_line:
                if nesting_level == 0:
                    # If we're not inside a nested block, this END indicates the end of the stored procedure/function
                    in_sp = False
                    processed_chunks.append(''.join(sp_chunk))
                    sp_chunk = []
                else:
                    # If inside a nested block, decrease the nesting level
                    nesting_level -= 1
            
            if nesting_level == 0 and not in_sp:
                # Finalize the chunk when the nesting level returns to zero and we're not in a procedure
                processed_chunks.append(''.join(sp_chunk))
                sp_chunk = []

    if sp_chunk:
        # Append the last chunk if the file does not end with 'END'
        processed_chunks.append(''.join(sp_chunk))

    if not processed_chunks:
        logging.warning("No valid stored procedures or functions found in the file.")
        return []

    return processed_chunks

def process_folder(folder_path, processing_type):

    """
    Processes all files in the given folder.
    
    Args:
        folder_path (str): The path to the folder containing the files.
        processing_type (str): The type of processing to perform.
    
    Returns:
        str: The processed content of all files.
    """
    if not os.path.exists(folder_path):
        logging.error(f"Folder not found: {folder_path}")
        raise FileNotFoundError(f"The folder {folder_path} does not exist.")
    
    if not os.path.isdir(folder_path):
        logging.error(f"Not a folder: {folder_path}")
        raise ValueError(f"The path {folder_path} is not a folder.")
    
    all_processed_content = []

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            try:
                file_content = reading_and_processing_file(file_path, processing_type)
                if file_content:
                    all_processed_content.extend(file_content)
                else:
                    logging.info(f"No useful content found in the file: {filename}")
            except (FileNotFoundError, ValueError) as e:
                logging.error(f"An error occurred with file {filename}: {e}")

    all_processed_content = [item for item in all_processed_content if item]
    return all_processed_content

class PDFWithBorder(FPDF):
    def header(self):
        self.set_line_width(0.8)  # 2mm thickness
        self.rect(2, 2, 206, 291)  # A4 size page: 210x297mm

def create_files(name, text_input, directory, additional_text=""):
    # Get current time and format it
    current_time = datetime.datetime.now().strftime("%H%M_%d-%m-%y")
    keyword = "target state code"
    
    # Define the additional keywords
    additional_keywords = ['name of the stored procedure', 'purpose of procedure', 'functionality overview']
    
    # Find the keyword (case insensitive)
    match = re.search(r'\*\*\s*target state code\s*:\s*\*\*', text_input, re.IGNORECASE)
    if not match:
        # Try a more relaxed fallback if markdown not present
        match = re.search(r'target state code\s*:?', text_input, re.IGNORECASE)

    if not match:
        raise ValueError("Keyword 'Target State Code' not found in the text.")

    index = match.start()
    
    # Split the text at the keyword
    before_keyword = text_input[:index].strip()
    after_keyword = text_input[index + len(keyword):].strip()
    
    # Create the directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    # Create PDF file with text before the keyword
    pdf_filename = os.path.join(directory, f"{name}_{current_time}.pdf")
    pdf = PDFWithBorder()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Split text into lines and add to PDF
    lines = before_keyword.split('\n')
    for line in lines:
        for keyword in additional_keywords:
            if keyword in line.lower():
                # Keyword found, make it bold and increase font size
                pdf.set_font("Arial", size=14, style='B')
                pdf.multi_cell(0, 10, line.encode('latin-1', errors='replace').decode('latin-1'))
                pdf.set_font("Arial", size=12)
                break
        else:
            try:
                pdf.multi_cell(0, 10, line.encode('latin-1', errors='replace').decode('latin-1'))
            except Exception as e:
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 10, line.encode('latin-1', errors='replace').decode('latin-1'))

    # Add additional text with heading
    pdf.set_font("Arial", size=12, style='B')
    pdf.ln(10)  # Add a new line
    pdf.cell(200, 10, txt="File Path of the Procedure", ln=True, align='L')
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, additional_text.encode('latin-1', errors='replace').decode('latin-1'))
    
    # Create text file with text after the keyword
    text_filename = os.path.join(directory, f"{name}_{current_time}.txt")
    with open(text_filename, 'w', encoding='utf-8', errors='replace') as text_file:
        text_file.write(after_keyword)
    
    # Add additional text with heading to PDF
    pdf.set_font("Arial", size=12, style='B')
    pdf.ln(10)  # Add a new line
    pdf.cell(200, 10, txt="File Path of the Target State Code", ln=True, align='L')
    pdf.set_font("Arial", size=12)
    absolute_path_text = os.path.abspath(text_filename)
    pdf.multi_cell(0, 10, absolute_path_text.encode('latin-1', errors='replace').decode('latin-1'))
    
    pdf.output(pdf_filename, 'F')
    print(f"PDF file created: {pdf_filename}")
    print(f"Text file created: {text_filename}")

def extract_details(input_text):
    # Extract details using regular expressions, handling cases with or without colons and multi-line content
    name_match = re.search(r"Name of the Stored Procedure[\s:]*([\s\S]*?)(?=Purpose of Procedure|$)", input_text, re.IGNORECASE)
    purpose_match = re.search(r"Purpose of Procedure[\s:]*([\s\S]*?)(?=Functionality Overview|$)", input_text, re.IGNORECASE)
    overview_match = re.search(r"Functionality Overview[\s:]*([\s\S]*?)(?=Target State Code|$)", input_text, re.IGNORECASE)
    target_code_match = re.search(r"Target State Code[\s:]*([\s\S]*)", input_text, re.IGNORECASE)

    # Extracted text parts, ensuring we strip extra newlines and whitespace
    name_of_stored_procedure = name_match.group(1).strip().replace('\n', ' ').strip() if name_match else "Unknown"
    purpose_of_procedure = purpose_match.group(1).strip().replace('\n', ' ').strip() if purpose_match else "Unknown"
    functionality_overview = overview_match.group(1).strip().replace('\n', ' ').strip() if overview_match else "Unknown"
    target_state_code = target_code_match.group(1).strip().replace('\n', ' ').strip() if target_code_match else "Unknown"
    
    return name_of_stored_procedure, purpose_of_procedure, functionality_overview, target_state_code

def remove_special_characters(s):
    # Keep only alphanumeric characters (letters and numbers)
    return re.sub(r'[^A-Za-z0-9]', '', s)

def gemini(g_key,stored_procedure_details,target_state_code):

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={g_key}"

    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        "contents": [
            # {
            #     "parts": [
            #         {"text": f"""You are a helpful assistant that converts Sybase stored procedures into requirement documents and {target_state_code}."""}
            #     ]
            # },
            {
                "parts": [
                    {"text": f"""
                    I have the following Sybase stored procedure details:

                    {stored_procedure_details}

                    The target state code should be executable and suitable for a production server. Note that the response should be in the below format only. Also, no need for new lines after individual points. But all the four headers should definetly be there with the same spellings.

                    Please generate the following:
                    1. Name of the Stored Procedure: Generate a name for this stored procedure. Just the name, dont write anything more or give any additional info.
                    2. Purpose of Procedure: Provide in one paragraph as to what is the use of this stored procedure.  
                    3. Functionality Overview: Provide a detailed explanation of what the stored procedure does, including the purpose of each variable.
                    4. Target State Code: Provide executable code that can be run on a production server.

                    Here is the initial target state code:
                    {target_state_code}

                    Generate the functionality overview and the final target state code.
                    """}
                ]
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data)

    # Print response
    print(response.status_code)
    print(response.json())
    return response.json()


def extract_text_from_gemini_response(input_data):
    # If it's a string, try to parse it
    if isinstance(input_data, str):
        try:
            input_data = json.loads(input_data)
        except json.JSONDecodeError as e:
            print("Invalid JSON string:", e)
            return None

    # Now input_data is a dictionary — try to extract the text
    try:
        return input_data['candidates'][0]['content']['parts'][0]['text']
    except (KeyError, IndexError, TypeError) as e:
        print("Failed to extract 'text':", e)
        return None

if __name__ == "__main__":
    file_path = config.file_path
    processing_type = "Sybase"
    key = config.api_key
    target_state = config.target_state
    result = process_folder(file_path, processing_type)
    for i, chunk in enumerate(result):
        response = gemini(key, chunk, target_state)
        print(response)
        text = extract_text_from_gemini_response(response)
        print("New Program Starts")
        print("\n")
        print(text)
        name_of_stored_procedure, purpose_of_procedure, functionality_overview, target_state_code = extract_details(text)
        name_of_stored_procedure = remove_special_characters(name_of_stored_procedure)
        create_files(name_of_stored_procedure, text, 'output_dir', file_path)