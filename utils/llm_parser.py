import google.generativeai as genai
import pandas as pd
from pypdf import PdfReader
import io
import json
import typing_extensions as typing
from openai import OpenAI
import os

def extract_text_from_pdf(pdf_file):
    """Extracts text from a PDF file."""
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def extract_text_from_pdf_range(pdf_file, start_page, end_page):
    """Extracts text from a PDF file within a specific page range (1-based)."""
    reader = PdfReader(pdf_file)
    text = ""
    # Adjust for 0-based indexing
    start_idx = max(0, start_page - 1)
    end_idx = min(len(reader.pages), end_page)
    
    for i in range(start_idx, end_idx):
        text += reader.pages[i].extract_text()
    return text

def extract_all_pages(pdf_file):
    """
    Extracts text from all pages of a PDF file.
    Returns a list of strings, where index i corresponds to page i+1.
    """
    reader = PdfReader(pdf_file)
    pages_text = []
    for page in reader.pages:
        pages_text.append(page.extract_text())
    return pages_text

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import google.api_core.exceptions

# Retry configuration: Retry up to 5 times, waiting exponentially (1s, 2s, 4s...)
@retry(
    retry=retry_if_exception_type(google.api_core.exceptions.ResourceExhausted),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=4, max=60)
)
def _generate_with_retry(model, prompt, generation_config):
    return model.generate_content(prompt, generation_config=generation_config)

def call_llm(prompt, model_choice="Gemini 3 Pro", json_mode=False):
    """
    Helper function to call the selected LLM.
    """
    try:
        if "Gemini" in model_choice:
            # Map UI name to API model name
            if "2.5" in model_choice:
                model_name = 'gemini-2.5-pro' 
            elif "3" in model_choice:
                model_name = 'gemini-3-pro-preview'
            elif "Flash" in model_choice:
                model_name = 'gemini-2.0-flash'
            else:
                model_name = 'gemini-3-pro-preview' # Default to 3 Pro

            model = genai.GenerativeModel(model_name)
            generation_config = {}
            if json_mode:
                generation_config["response_mime_type"] = "application/json"
            
            # Use the retry-wrapped function
            response = _generate_with_retry(model, prompt, generation_config)
            
            # Robust response handling
            if response and response.candidates:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    return response.text
                else:
                    print(f"Warning: Gemini returned no content. Finish Reason: {candidate.finish_reason}")
                    if candidate.safety_ratings:
                        print(f"Safety Ratings: {candidate.safety_ratings}")
                    return ""
            else:
                print("Error: Gemini response contained no candidates.")
                return ""

        elif "ChatGPT" in model_choice or "gpt" in model_choice.lower():
            # OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            model_name = "gpt-4o-mini" # User asked for "ChatGPT 5 mini", mapping to 4o-mini as the closest real equivalent.
            
            messages = [{"role": "user", "content": prompt}]
            
            response_format = None
            if json_mode:
                response_format = {"type": "json_object"}

            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                response_format=response_format
            )
            return response.choices[0].message.content
            
    except Exception as e:
        print(f"Error calling LLM ({model_choice}): {e}")
        return ""
    return ""

def parse_catalog_toc(text, catalog_name, academic_year="2025-2026", model_choice="Gemini 2.5 Pro"):
    """
    Parses the catalog ToC text using Gemini to extract programs.
    Returns a list of dictionaries.
    """
    # model = genai.GenerativeModel('gemini-2.5-pro') # Moved to call_llm

    # Determine Start Point logic based on catalog name
    start_point_instruction = ""
    if "Graduate" in catalog_name:
        if "2024-2025" in academic_year:
             start_point_instruction = '- **Start Point**: The list of relevant programs typically starts with "Accountancy and Analytics". Ignore entries before that.'
        else:
             start_point_instruction = "" # Allow LLM to find all programs, effectively removing the start point restriction


    prompt_2526 = f"""
    You are an expert at parsing university catalog Tables of Contents.
    You are currently parsing the **{{catalog_name}}**.
    Your task is to extract a list of academic programs from the provided text.
    
    The text contains lines with Program Names, Credentials, and Page Numbers, often connected by dots (e.g., "Program Name ...... 123").
    
    **CRITICAL EXCLUSION CRITERIA:**
    - **Exclude Concurrent Degrees**: Do NOT include entries that list multiple degrees joined by "and" (e.g., "Anthropology, M.A. and Public Health, M.P.H.").
    {start_point_instruction}
    - **Exclude Credential-First Entries**: Do NOT include entries where the credential comes BEFORE the program name (e.g., "B.S. in Biomedical Sciences"). The program name must come first.

    **INCLUSION CRITERIA (Undergraduate):**
    - **Include Minors**: (e.g., "Addictions Studies Minor"). Treat "Minor" as the credential.
    - **Include Concentrations**: (e.g., "Criminology B.A., with Cybercrime Concentration"). Include the full concentration details.
    - **Include Concentrations**: (e.g., "Criminology B.A., with Cybercrime Concentration"). Include the full concentration details.
    - **Include Exploratory Curriculum**: (e.g., "Exploratory Curriculum: Arts and Humanities Pathway"). These do not have a credential. Use "N/A" as the credential.
    
    **HANDLING MULTI-LINE ENTRIES:**
    - Some program names may span multiple lines in the text.
    - If a line ends without a page number and the next line continues the name (or starts with "Concentration"), combine them.
    - **Separated Page Numbers**: Sometimes the program name is on one line, and the page number is on the next line, preceded by dots (e.g., "Program Name \\n ........... 123"). Treat this as one entry.
    - **Look ahead** to capture the full name and page number if they are split across lines.

    **OUTPUT FORMAT:**
    - Output each program on a new line.
    - Use a pipe character "|" to separate Original Text, Program Name, Credential, and Page Number.
    - Format: `Original Text | Program Name | Credential | Page Number`
    - **Original Text**: The exact text of the program and credential as it appears in the catalog, but WITHOUT the trailing dots or page number. Preserve punctuation (or lack thereof) between name and credential. If the text spans multiple lines, join them with a space.
    - **Clean the Data**: Remove "..." and any page numbers from the Program Name. Remove whitespace.
    
    **Examples:**
    Artificial Intelligence, M.S.A.I. | Artificial Intelligence | M.S.A.I. | 153
    Computer Engineering B.S.C.P. | Computer Engineering | B.S.C.P. | 164
    Studio Art B.F.A. | Studio Art | B.F.A. | 496
    Addictions Studies Minor | Addictions Studies | Minor | 123
    Criminology B.A., with Cybercrime Concentration | Criminology | B.A., with Cybercrime Concentration | 200
    Exploratory Curriculum: Arts and Humanities Pathway | Exploratory Curriculum: Arts and Humanities Pathway | N/A | 805

    Text to parse:
    {text}
    """

    prompt_2425 = f"""
    You are an expert at parsing university catalog Tables of Contents.
    You are currently parsing the **{{catalog_name}}**.
    Your task is to extract a list of academic programs from the provided text.

    The text contains lines with Program Names, Credentials, and Page Numbers, often connected by dots.
    
    **CRITICAL EXCLUSION CRITERIA:**
    - **Exclude "Admission Information"**: The Graduate catalog often has lines saying "Admission Information" below the program name. IGNORE these lines completely.
    - **Exclude Concurrent Degrees**: Do NOT include entries that list multiple degrees joined by "and".
    - **Exclude Credential-First Entries**: Do NOT include entries where the credential comes BEFORE the program name.
    {start_point_instruction}

    **INCLUSION CRITERIA:**
    - **Include Degrees**: (e.g., "Accounting, M.Acc.", "Biology, B.S.").
    - **Include Minors**: (e.g., "Africana Studies Minor").
    - **Include Concentrations**: (e.g., "Criminology B.A., with Cybercrime Concentration").
    - **Include Exploratory Curriculum**: (e.g., "Exploratory Curriculum: Arts and Humanities Pathway"). These do not have a credential. Use "N/A" as the credential.
    
    **HANDLING MULTI-LINE ENTRIES:**
    - Some program names may span multiple lines. Combine them if the first line has no page number.
    - **Separated Page Numbers**: If the page number is on the next line, treat it as one entry.

    **OUTPUT FORMAT:**
    - Output each program on a new line.
    - Use a pipe character "|" to separate Original Text, Program Name, Credential, and Page Number.
    - Format: `Original Text | Program Name | Credential | Page Number`
    - **Original Text**: The exact text of the program and credential as it appears in the catalog, but WITHOUT the trailing dots or page number.
    - **Clean the Data**: Remove "..." and any page numbers from the Program Name. Remove whitespace.
    
    **Examples:**
    Advertising, M.S. | Advertising | M.S. | 215
    Africana Studies Minor | Africana Studies | Minor | 141
    Biology, Ph.D. | Biology | Ph.D. | 231
    Cancer Biology, Ph.D. | Cancer Biology | Ph.D. | 239

    Text to parse:
    {text}
    """

    # Select Prompt based on Academic Year
    if "2024-2025" in academic_year:
        prompt = prompt_2425
    else:
        prompt = prompt_2526
    
    try:
        response_text = call_llm(prompt, model_choice)
        
        data = []
        lines = response_text.strip().split('\n')
        for line in lines:
            parts = line.split('|')
            if len(parts) == 4:
                original_text = parts[0].strip()
                program_name = parts[1].strip()
                credential = parts[2].strip()
                page_number_str = parts[3].strip()
                
                # Basic validation
                if program_name and credential and page_number_str.isdigit():
                    # EXCLUSION FILTER: Remove Catalog Headers mistakenly identified as programs
                    header_keywords = ["Catalog", "University", "South Florida", "USF Graduate", "USF Undergraduate"]
                    if any(kw in program_name for kw in header_keywords) or any(kw in original_text for kw in header_keywords):
                        continue

                    data.append({
                        "original_text": original_text,
                        "program_name": program_name,
                        "credential": credential,
                        "page_number": int(page_number_str),
                        "catalog_name": catalog_name
                    })
        
        return data

    except Exception as e:
        print(f"Error parsing with LLM: {e}")
        try:
            print(f"Raw response: {response_text[:500]}...") 
        except:
            pass
        return []

def validate_catalog_type(programs, catalog_type):
    """
    Filters programs based on catalog type (ug or gr) and credential.
    """
    valid_programs = []
    
    # Define invalid prefixes/substrings for each type
    # If catalog is GR, exclude UG credentials
    invalid_gr_credentials = ["B.", "Minor", "Certificate"] 
    
    # If catalog is UG, exclude GR credentials
    invalid_ug_credentials = ["M.", "Ph.D", "Dr.", "Ed.D", "Au.D", "D.B.A", "D.N.P", "D.P.T", "Pharm.D", "Ed.S", "Graduate Certificate"]

    # List of all credentials to check for "Credential First" pattern
    all_credentials = invalid_gr_credentials + invalid_ug_credentials + ["B.S.", "B.A.", "B.F.A.", "B.G.S.", "M.S.", "M.A."]

    for p in programs:
        cred = p.get('credential', '').strip()
        orig_text = p.get('original_text', '').strip()
        
        # 1. Check for "Credential First" pattern (Invalid)
        # e.g. "B.S. in Biomedical Sciences"
        if any(orig_text.startswith(c + " ") or orig_text.startswith(c + "in ") for c in all_credentials):
             continue # Skip this program

        if catalog_type == 'gr':
            # Check if credential looks like UG
            is_invalid = False
            for inv in invalid_gr_credentials:
                if cred.startswith(inv) or inv in cred:
                    # Special case: "M.B.A." starts with "M." so it's fine for GR.
                    # But we are checking for "B." for GR.
                    # "B.S." starts with "B.". "Minor" is in "Minor".
                    
                    # Refined check for "B.":
                    if inv == "B." and cred.startswith("B."):
                        is_invalid = True
                        break
                    if inv == "Minor" and "Minor" in cred:
                        is_invalid = True
                        break
                    # Refined check for "Certificate":
                    # Only exclude if it's just "Certificate" (UG) or doesn't contain "Graduate"
                    if inv == "Certificate" and "Certificate" in cred and "Graduate" not in cred:
                         is_invalid = True
                         break
                    # Exclude "N/A" credential from Graduate (Exploratory Curriculum is UG)
                    if cred == "N/A":
                        is_invalid = True
                        break
            
            if not is_invalid:
                valid_programs.append(p)

        elif catalog_type == 'ug':
            # Check if credential looks like GR
            is_invalid = False
            for inv in invalid_ug_credentials:
                if cred.startswith(inv):
                    is_invalid = True
                    break
                if "Graduate" in cred:
                    is_invalid = True
                    break
            
            # "N/A" is allowed for UG (Exploratory Curriculum)
            
            if not is_invalid:
                valid_programs.append(p)
    
    return valid_programs

def filter_programs(programs, min_page, max_page):
    """
    Filters the list of programs based on page number criteria.
    """
    filtered = []
    for p in programs:
        try:
            page_num = int(p.get('page_number', -1))
            if min_page <= page_num <= max_page:
                filtered.append(p)
        except ValueError:
            continue # Skip if page number is not an integer
    return filtered

def parse_full_catalog_programs(text, catalog_name, model_choice="Gemini 2.5 Pro"):
    """
    Parses the full catalog text to extract programs.
    This uses a prompt tailored for full text extraction, ignoring policies etc.
    """
    # model = genai.GenerativeModel('gemini-2.5-pro') # Moved to call_llm

    prompt = f"""
    You are an expert at parsing university catalogs.
    Your task is to extract a comprehensive list of academic programs (Degrees, Majors, Minors, Certificates) from the provided full catalog text.
    
    The text contains the entire catalog, including policies, course descriptions, and other non-program information. 
    You must focus ONLY on the sections listing the academic programs offered.

    **CRITICAL EXCLUSION CRITERIA:**
    - **Exclude Policies & General Info**: Ignore admission requirements, tuition, code of conduct, etc.
    - **Exclude Course Descriptions**: Do not list individual courses (e.g., "ENG 101 - English Composition").
    - **Exclude Concurrent Degrees**: Do NOT include entries that list multiple degrees joined by "and" (e.g., "Anthropology, M.A. and Public Health, M.P.H.").
    - **Exclude Credential-First Entries**: Do NOT include entries where the credential comes BEFORE the program name (e.g., "B.S. in Biomedical Sciences"). The program name must come first.

    **INCLUSION CRITERIA:**
    - **Include Degrees**: (e.g., "Computer Science, B.S.", "English, M.A.", "Education, Ph.D.").
    - **Include Minors**: (e.g., "History Minor").
    - **Include Certificates**: (e.g., "Data Science Certificate", "Leadership Graduate Certificate").
    - **Include Concentrations**: (e.g., "Criminology B.A., with Cybercrime Concentration").
    
    **OUTPUT FORMAT:**
    - Output each program on a new line.
    - Use a pipe character "|" to separate Original Text, Program Name, and Credential.
    - Format: `Original Text | Program Name | Credential`
    - **Original Text**: The exact text of the program and credential as found.
    - **Program Name**: The name of the program (e.g., "Computer Science").
    - **Credential**: The degree or certificate type (e.g., "B.S.", "Minor", "M.A.", "Ph.D.", "Certificate").
    
    **Examples:**
    Artificial Intelligence, M.S.A.I. | Artificial Intelligence | M.S.A.I.
    Computer Engineering B.S.C.P. | Computer Engineering | B.S.C.P.
    Addictions Studies Minor | Addictions Studies | Minor
    Criminology B.A., with Cybercrime Concentration | Criminology | B.A., with Cybercrime Concentration
    
    Text to parse:
    {text}
    """
    
    try:
        response_text = call_llm(prompt, model_choice)
        
        data = []
        lines = response_text.strip().split('\\n')
        for line in lines:
            parts = line.split('|')
            if len(parts) >= 3: # Expecting at least 3 parts
                original_text = parts[0].strip()
                program_name = parts[1].strip()
                credential = parts[2].strip()
                
                # Basic validation
                if program_name and credential:
                    data.append({
                        "original_text": original_text,
                        "program_name": program_name,
                        "credential": credential,
                        "catalog_name": catalog_name,
                        # Page number is harder to pinpoint in full text without specific markers, 
                        # so we might omit it or set to 0/None for this report type if not strictly needed for the report columns requested.
                        # The user request didn't explicitly ask for page numbers in the 3 columns, but it's good practice.
                        # For now, we'll leave it out or set to 0.
                        "page_number": 0 
                    })
        
        return data

    except Exception as e:
        print(f"Error parsing full catalog with LLM: {e}")
        return []

def get_educational_objective(credential, catalog_type):
    """
    Determines the Educational Objective based on the credential and catalog type.
    """
    cred_lower = credential.lower()
    
    # Check for Certificates first
    if "certificate" in cred_lower:
        if "graduate" in cred_lower or catalog_type == 'gr':
            return "Grad Cert"
        else:
            return "Certificate" # Undergraduate Certificate
            
    # Check for Doctorate
    if any(x in cred_lower for x in ["ph.d", "ed.d", "au.d", "d.b.a", "d.n.p", "d.p.t", "pharm.d", "doctor"]):
        return "Doctorate"
        
    # Check for Masters
    if any(x in cred_lower for x in ["m.s.", "m.a.", "m.b.a", "m.ed", "m.p.h", "m.s.w", "master", "ed.s"]): # Ed.S is often grouped with Grad/Masters level
         return "Masters"

    # Check for Bachelors
    if any(x in cred_lower for x in ["b.s.", "b.a.", "b.f.a", "b.g.s", "bachelor"]):
        return "Bachelor"
    
    # Fallback/Default logic
    if catalog_type == 'ug':
        return "Bachelor" # Default for UG if not certificate
    elif catalog_type == 'gr':
        return "Masters" # Default for GR if not doctorate/cert
        
    return "Unknown"

def has_concentration(program_name):
    """
    Checks if the program name implies a concentration.
    """
    if "concentration" in program_name.lower():
        return "Yes"
    return "No"

def parse_program_details(text, program_name, credential, catalog_type, academic_year="2025-2026", model_choice="Gemini 2.5 Pro"):
    """
    Analyzes the program text to determine Accreditation, Educational Objective, and Concentrations.
    """
    # model = genai.GenerativeModel('gemini-2.5-pro') # Moved to call_llm

    prompt_2526 = f"""
    You are analyzing the catalog entry for the academic program: "{program_name}" with credential "{credential}".
    
    Based on the provided text, determine the following:
    1. **Accredited**: Is the program accredited? Return "No" ONLY if the text EXPLICITLY states it is "not accredited" or "pending accreditation". Otherwise, return "Yes".
    2. **Educational Objective**: What is the level of this program? Choose one: "Bachelor", "Certificate", "Masters", "Doctorate", "Grad Cert".
       - Use the credential "{credential}" as the primary guide.
       - "B.S.", "B.A." -> "Bachelor"
       - "Minor" -> "Bachelor"
       - "M.S.", "M.A." -> "Masters"
       - "Ph.D.", "Ed.D." -> "Doctorate"
       - "Certificate" (Undergraduate) -> "Certificate"
       - "Graduate Certificate" -> "Grad Cert"
    3. **Concentrations**: Does this program offer concentrations?
       - **Graduate Programs (Masters, Doctorate, Grad Cert)**: Return "Yes" if the text lists concentrations (often under a "Concentrations:" header). Otherwise, return "No".
       - **Minors and Certificates**: Return "No".
       - **Undergraduate Degrees**: Return "Yes" ONLY if the Program Name explicitly includes the word "Concentration" (e.g., "B.A. with Cybercrime Concentration").
       - If the word "Concentration" is NOT in the Program Name title itself, return "No", even if the text mentions tracks or specializations.
    4. **Total_Credit_Hours**: What is the total number of credit hours required for this degree?
       
       **How to interpret the text:**
       - Read the program description like a human would.
       - Identify the official credit hour total stated for the full degree or certificate.
       - **Do not confuse individual course credits with total program credits.**

       **What counts as the official total:**
       - Look for phrases like: "Total Minimum Hours", "Total Program Hours", "Total Minimum Credit Hours", "Minimum Hours", "Post-Bachelor’s Minimum Hours", "Program requires N total credit hours", "Graduate Certificate requires N credit hours".
       - **Graduate Certificates**: Look for "Curriculum Requirements (X Credit Hours)" or "Graduate Certificate Requirements: X credit hours". Treat X as the total.
       - Treat all of these as meaning the same thing: total required hours for graduation.
       - Interpret meaning, don't match phrases literally.

       **How to handle multiple hour values:**
       - If both post-bachelor and post-master totals are listed, **use the post-bachelor total**.
       - If unclear, choose the larger number (representing the full program load).
       - Example: "72 hours post-bachelor, 42 post-master" -> return "72".

       **What to IGNORE (Very Important):**
       - **Do not use course-level credits.**
       - Ignore lines like "Credit Hours: 3", "3 credit hours each", or lists of courses.
       - Only rely on the explicitly stated full program requirement.

       **Output:**
       - Return ONLY the numeric value (e.g., "30", "72", "9").
       - If no total is stated anywhere after reviewing the text, return "Unknown".

    5. **License_Prep**: Does this program prepare students for professional licensure?
       - Return "Yes" ONLY if the text explicitly states that the program prepares students for licensure, certification exams, or meets state requirements for a license (e.g., "prepares students for the CPA exam", "meets requirements for nursing licensure", "leads to state certification").
       - Otherwise, return "No".

    6. **Modality**: What is the primary means of instruction delivery?
       - **"Distant"**: If the text explicitly states the program is offered "entirely online", "fully online", "100% online", or "exclusively online".
       - **"Both"**: If the text states the program is offered "both on-campus and online", "hybrid", or available in "both formats".
       - **"Resident"**: Default value. Use this if neither of the above are explicitly stated, or if it says "on-campus", "face-to-face", or "in-person".

    **OUTPUT FORMAT:**
    Return a JSON object with keys: "Accredited", "Educational_Objective", "Concentrations", "Total_Credit_Hours", "License_Prep", "Modality".
    Example: {{"Accredited": "Yes", "Educational_Objective": "Bachelor", "Concentrations": "No", "Total_Credit_Hours": "120", "License_Prep": "No", "Modality": "Resident"}}

    Text to analyze:
    {text}
    """

    prompt_2425 = f"""
    You are analyzing the catalog entry for the academic program: "{program_name}" with credential "{credential}".
    
    Based on the provided text, determine the following:
    1. **Accredited**: Is the program accredited? Return "No" ONLY if the text EXPLICITLY states it is "not accredited" or "pending accreditation". Otherwise, return "Yes".
    2. **Educational Objective**: What is the level of this program? Choose one: "Bachelor", "Certificate", "Masters", "Doctorate", "Grad Cert".
       - Use the credential "{credential}" as the primary guide.
       - "B.S.", "B.A." -> "Bachelor"
       - "Minor" -> "Bachelor"
       - "M.S.", "M.A." -> "Masters"
       - "Ph.D.", "Ed.D." -> "Doctorate"
       - "Certificate" (Undergraduate) -> "Certificate"
       - "Graduate Certificate" -> "Grad Cert"
    3. **Concentrations**: Does this program offer concentrations?
       - **Graduate Programs (Masters, Doctorate, Grad Cert)**: Return "Yes" if the text lists concentrations (often under a "Concentrations:" header). Otherwise, return "No".
       - **Minors and Certificates**: Return "No".
       - **Undergraduate Degrees**: Return "Yes" ONLY if the Program Name explicitly includes the word "Concentration" (e.g., "B.A. with Cybercrime Concentration").
       - If the word "Concentration" is NOT in the Program Name title itself, return "No", even if the text mentions tracks or specializations.
    4. **Total_Credit_Hours**: What is the total number of credit hours required for this degree?
       
       **How to interpret the text (2024-2025 Format):**
       - Look for the section **"REQUIRED COURSES: (X CREDIT HOURS)"**. The value X is often the major requirement.
       - Look for **"STATE MANDATED COMMON COURSE PREREQUISITES ... (Y CREDIT HOURS)"**.
       - Look for **"Total Minimum Hours"** or similar phrases.
       - **If "Total Minimum Hours" is explicitly stated, use that.**
       - **If NOT stated, but you see "REQUIRED COURSES: (X CREDIT HOURS)", use X.** (Note: This might be just the major hours, but it's the best proxy if total is missing).
       - **Graduate Certificates**: Look for "Curriculum Requirements (X Credit Hours)".

       **What to IGNORE (Very Important):**
       - **Do not use course-level credits.**
       - Ignore lines like "Credit Hours: 3", "3 credit hours each".

       **Output:**
       - Return ONLY the numeric value (e.g., "30", "72", "9").
       - If no total is stated anywhere after reviewing the text, return "Unknown".

    5. **License_Prep**: Does this program prepare students for professional licensure?
       - Return "Yes" ONLY if the text explicitly states that the program prepares students for licensure, certification exams, or meets state requirements for a license.
       - Otherwise, return "No".

    6. **Modality**: What is the primary means of instruction delivery?
       - **"Distant"**: If the text explicitly states the program is offered "entirely online", "fully online", "100% online", or "exclusively online".
       - **"Both"**: If the text states the program is offered "both on-campus and online", "hybrid", or available in "both formats".
       - **"Resident"**: Default value. Use this if neither of the above are explicitly stated, or if it says "on-campus", "face-to-face", or "in-person".

    **OUTPUT FORMAT:**
    Return a JSON object with keys: "Accredited", "Educational_Objective", "Concentrations", "Total_Credit_Hours", "License_Prep", "Modality".
    Example: {{"Accredited": "Yes", "Educational_Objective": "Bachelor", "Concentrations": "No", "Total_Credit_Hours": "120", "License_Prep": "No", "Modality": "Resident"}}

    Text to analyze:
    {text}
    """

    # Select Prompt based on Academic Year
    if "2024-2025" in academic_year:
        prompt = prompt_2425
    else:
        prompt = prompt_2526
    
    try:
        response_text = call_llm(prompt, model_choice, json_mode=True)
        return json.loads(response_text)
    except Exception as e:
        print(f"Error parsing details for {program_name}: {e}")
        # Fallback using helpers
        return {
            "Accredited": "Yes",
            "Educational_Objective": get_educational_objective(credential, catalog_type),
            "Concentrations": has_concentration(program_name),
            "Total_Credit_Hours": "Unknown"
        }

