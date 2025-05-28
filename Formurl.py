import requests
import re
import json
import os
from urllib.parse import urlparse, urlencode
import google.generativeai as genai
from typing import Dict, List, Optional

#https://docs.google.com/forms/d/e/1FAIpQLSdVh3dJt_0ZfEHGlo--uQl9ewe3kajePbw8K6Dlq785dBDbew/viewform

# Initialize Gemini API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

class GoogleFormHandler:
    def __init__(self):
        if GOOGLE_API_KEY:
            try:
                self.model = genai.GenerativeModel('models/gemini-2.0-flash')
            except Exception as e:
                print(f"Error initializing Gemini model: {e}")
                self.model = None
        else:
            self.model = None
            print("Google API Key not found. AI features will be disabled.")

    def get_user_data_content(self, file_path='userdata.txt') -> str:
        """Reads the raw content of the user data file."""
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return f.read()
        print(f"Warning: User data file '{file_path}' not found or is empty.")
        return "User data file not found or is empty."

    def extract_primary_email_from_userdata(self, user_data_content: str) -> Optional[str]:
        """Extracts the primary email address from userdata.txt content."""
        email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        lines = user_data_content.split('\n')
        for line in lines:
            line_lower = line.lower()
            if line_lower.startswith("email -") or line_lower.startswith("email:") or "primary email" in line_lower:
                match = re.search(email_regex, line)
                if match:
                    return match.group(0).strip()
        first_email_found = re.search(email_regex, user_data_content)
        if first_email_found:
            return first_email_found.group(0).strip()
        return None

    def get_form_source(self, url: str) -> Optional[str]:
        """Fetch the source code of a Google Form."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching form: {e}")
            return None

    def extract_form_data(self, source_code: str) -> Optional[list]:
        """Extract form data from the source code."""
        if not source_code:
            return None
        
        match = re.search(r'var FB_PUBLIC_LOAD_DATA_ = (.*?);', source_code, re.DOTALL)
        if not match:
            print("Could not find FB_PUBLIC_LOAD_DATA_ in source code. Form structure might be different or page not fully loaded.")
            return None
        
        data_str = match.group(1)
        
        # Attempt to fix common JSON issues before parsing
        # 1. Escape unescaped newlines within strings (common cause of "Unterminated string")
        # This regex looks for a newline that is NOT preceded by a backslash (already escaped)
        # and is within a string (by roughly checking for surrounding quotes, not perfectly robust but helps)
        # A truly robust solution for arbitrary unescaped characters in JS pseudo-JSON is very complex.
        data_str_cleaned = re.sub(r'(?<!\\)\n', r'\\n', data_str)
        data_str_cleaned = re.sub(r'(?<!\\)\r', r'\\r', data_str_cleaned)
        
        # 2. Remove trailing commas before ] or }
        data_str_cleaned = re.sub(r',(\s*[\]\}])', r'\1', data_str_cleaned)
        
        try:
            form_data = json.loads(data_str_cleaned)
            print("Successfully parsed FB_PUBLIC_LOAD_DATA_ after cleaning.")
            return form_data
        except json.JSONDecodeError as e:
            print(f"Error parsing form data (FB_PUBLIC_LOAD_DATA_) even after cleaning: {e}.")
            print(f"Cleaned data (first 500 chars): {data_str_cleaned[:500]}...")
            # As a last resort, try parsing the original string if cleaning failed
            if data_str_cleaned != data_str:
                try:
                    print("Attempting to parse original FB_PUBLIC_LOAD_DATA_ string...")
                    form_data_original = json.loads(data_str)
                    print("Successfully parsed original FB_PUBLIC_LOAD_DATA_.")
                    return form_data_original
                except json.JSONDecodeError as e2:
                    print(f"Error parsing original form data string as well: {e2}.")
                    print(f"Original data (first 500 chars): {data_str[:500]}...")
            return None

    def extract_questions(self, form_data: list) -> Dict[str, dict]:
        if not form_data or not isinstance(form_data, list) or len(form_data) < 2 or form_data[1] is None:
            print("Form data structure is not as expected for question extraction (form_data[1] is None or too short).")
            return {}
        
        questions = {}
        form_description_and_questions = form_data[1]
        if not isinstance(form_description_and_questions, list) or len(form_description_and_questions) < 2:
            print("Form data structure is not as expected (form_description_and_questions issue).")
            return {}

        form_questions_list = form_description_and_questions[1]
        if not form_questions_list: 
            print("No questions found in the form structure (form_questions_list is empty/None).")
            return {}
        
        for question_data_list in form_questions_list:
            if not isinstance(question_data_list, list) or len(question_data_list) < 2:
                continue 

            question_text = str(question_data_list[1]) if question_data_list[1] is not None else "No question text"
            question_type_raw = question_data_list[3] 
            
            question_id = None
            options = []
            
            if len(question_data_list) >= 5 and isinstance(question_data_list[4], list) and question_data_list[4]:
                question_params_list = question_data_list[4]
                if question_params_list and isinstance(question_params_list[0], list) and len(question_params_list[0]) > 0:
                    question_id = question_params_list[0][0]
                    
                    if len(question_params_list[0]) >= 2 and isinstance(question_params_list[0][1], list):
                        raw_options = question_params_list[0][1]
                        for opt_list in raw_options:
                            if isinstance(opt_list, list) and len(opt_list) > 0 and opt_list[0] is not None:
                                options.append(str(opt_list[0])) 
            
            if question_id is not None:
                questions[str(question_id)] = {
                    'text': question_text,
                    'type': question_type_raw, 
                    'options': options
                }
        
        if not questions:
            print("Warning: No questions were successfully extracted. The form structure might be different than expected or form has no input fields.")
        return questions

    def generate_answers(self, questions: Dict[str, dict]) -> Dict[str, str]:
        if not self.model:
            print("Gemini model not initialized. AI features disabled.")
            manual_answers = {}
            print("\nPlease manually enter answers for the questions:")
            for q_id, q_data in questions.items():
                manual_answers[q_id] = input(f"{q_data['text']} (Options: {q_data.get('options', [])}): ")
            return manual_answers

        user_data_content = self.get_user_data_content()
        user_primary_email = self.extract_primary_email_from_userdata(user_data_content)
        is_optimist = "optimist: true" in user_data_content.lower() 
        
        answers = {}
        print("\nGenerating answers using AI...")
        email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        email_confirm_keywords = ["use", "confirm", "record", "include", "verify", "yes, this is", "select this email"]

        for q_id, q_data in questions.items():
            question_text_for_prompt = q_data['text']
            is_choice_question = q_data['type'] in [2, 3, 4] and q_data['options'] # 2:MC, 3:Dropdown, 4:Checkboxes

            if is_choice_question and user_primary_email:
                for option_text in q_data['options']:
                    option_lower = option_text.lower()
                    contains_keyword = any(keyword in option_lower for keyword in email_confirm_keywords)
                    if "email" in option_lower and contains_keyword:
                        match = re.search(email_regex, option_text)
                        if match:
                            email_in_option = match.group(0).strip()
                            if email_in_option.lower() == user_primary_email.lower():
                                answers[q_id] = option_text 
                                print(f"AI (Auto-selected email '{email_in_option}' for '{q_data['text']}'): {option_text}")
                                break 
                if q_id in answers: 
                    continue

            if is_choice_question and 'rating' in question_text_for_prompt.lower() and is_optimist and q_data['options']:
                answers[q_id] = q_data['options'][-1]
                print(f"AI (Optimist Override for '{q_data['text']}'): {answers[q_id]}")
                continue
            
            context = f"""You are a precise form-filling assistant. Your task is to provide a direct and concise answer for a single Google Form question.
Based on the user's information provided below, answer the following question.

USER INFORMATION (from userdata.txt):
---
{user_data_content}
---

QUESTION TO ANSWER:
{question_text_for_prompt}

Provide ONLY the exact answer that should be filled in the form field for this question. No explanations, no conversational text, just the answer itself. If the question asks for a choice from options, your answer MUST be one of the provided options.
"""
            if is_choice_question:
                context += f"Available options for this question: {json.dumps(q_data['options'])}\n"
            
            try:
                response = self.model.generate_content(context)
                ai_answer = response.text.strip()
                ai_answer = ai_answer.split('\n')[0]
                ai_answer = ai_answer.replace("Answer:", "").replace("\"", "").strip()

                if is_choice_question:
                    matched_option = None
                    for option in q_data['options']:
                        if option.strip().lower() == ai_answer.strip().lower():
                            matched_option = option
                            break
                    if not matched_option:
                         for option in q_data['options']:
                            if option.strip().lower() in ai_answer.strip().lower(): 
                                matched_option = option
                                break
                    answers[q_id] = matched_option if matched_option else (q_data['options'][0] if q_data['options'] else "")
                else: 
                    answers[q_id] = ai_answer
                
                print(f"AI (For '{q_data['text']}'): {answers[q_id]}")

            except Exception as e:
                print(f"Error generating AI answer for question '{q_data['text']}': {e}")
                if is_choice_question and q_data['options']:
                    answers[q_id] = q_data['options'][0] 
                else:
                    answers[q_id] = "Error: No AI answer"
        return answers

    def generate_prefilled_url(self, base_url: str, answers: Dict[str, str]) -> Optional[str]:
        parsed_url = urlparse(base_url)
        form_id_match = re.search(r'/forms/d/e/([^/]+)/viewform', base_url)
        if not form_id_match:
            path_parts = parsed_url.path.split('/')
            form_id = None
            if 'd' in path_parts and 'e' in path_parts:
                try:
                    d_index = path_parts.index('d')
                    if d_index + 2 < len(path_parts):
                        form_id = path_parts[d_index + 2]
                except ValueError:
                    pass 
            if not form_id:
                 print("Could not extract form ID from URL.")
                 return None
        else:
            form_id = form_id_match.group(1)

        base_form_url = f"https://docs.google.com/forms/d/e/{form_id}/viewform"
        params = {'usp': 'pp_url'}
        for question_id, answer in answers.items():
            params[f'entry.{question_id}'] = str(answer) 
        return f"{base_form_url}?{urlencode(params)}"

def main():
    if not GOOGLE_API_KEY:
        print("Google API Key not found. Please set your GOOGLE_API_KEY environment variable.")
        if input("Proceed without AI-assisted form filling? (y/n): ").lower() != 'y':
            return

    handler = GoogleFormHandler()
    form_url = input("Enter the Google Form URL: ").strip()
    if not form_url:
        print("No form URL entered. Exiting.")
        return

    source_code = handler.get_form_source(form_url)
    if not source_code:
        return

    form_data = handler.extract_form_data(source_code)
    if not form_data:
        print("Could not extract form data. Ensure the URL is a public Google Form and the structure is standard.")
        return

    questions = handler.extract_questions(form_data)
    if not questions:
        print("No questions were extracted. The form might be empty, or its structure might be incompatible.")
        return

    print("\nFound questions:")
    for q_id, q_data in questions.items():
        print(f"  ID: {q_id} - Question: {q_data['text']} (Type: {q_data['type']})")
        if q_data['options']:
            print(f"    Options: {json.dumps(q_data['options'])}")

    answers = handler.generate_answers(questions)
    
    if not answers:
        print("Failed to generate any answers.")
        return

    print("\nReview generated answers:")
    all_answers_valid = True
    for q_id, answer in answers.items():
        question_text = questions.get(str(q_id), {}).get('text', f"Unknown Question ID: {q_id}")
        print(f"  Q: {question_text}")
        print(f"  A: {answer}")
        if answer == "Error: No AI answer" or not answer.strip():
            if questions.get(str(q_id), {}).get('type') != 1: 
                 all_answers_valid = False
    
    if not all_answers_valid:
        print("\nWarning: Some answers could not be generated by AI or are empty for non-paragraph questions.")

    confirm = input("\nDo you want to proceed and open the pre-filled form? (y/n): ").lower()
    if confirm != 'y':
        print("Operation cancelled by user.")
        return

    prefilled_url = handler.generate_prefilled_url(form_url, answers)
    if prefilled_url:
        print(f"\nPre-filled URL (for review):\n{prefilled_url}")
        try:
            import webbrowser
            webbrowser.open(prefilled_url)
            print("Attempted to open the pre-filled URL in your browser.")
        except Exception as e:
            print(f"Could not open browser: {e}. Please copy the URL manually.")
    else:
        print("Could not generate the pre-filled URL.")

if __name__ == "__main__":
    main()