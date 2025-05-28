# Google Form Autofiller AI

An intelligent Python script to automatically fill out Google Forms using Google's Gemini AI, designed to save you time on repetitive form entries.

## Description

This project provides a command-line tool that takes a Google Form URL, parses its questions, and uses the Gemini generative AI model to provide answers based on user-provided data. It intelligently handles various question types, including text fields, multiple-choice, dropdowns, and even has an "optimist" mode for rating questions.

The script fetches the form structure, extracts questions and their IDs, and then for each question, queries the Gemini AI with the question text and the user's personal data (from `userdata.txt`) as context to generate an appropriate answer. Finally, it constructs a pre-filled URL that can be opened in a browser for review before submission.

## Features

*   **AI-Powered Answers**: Leverages Google's Gemini AI (via API) to generate contextually relevant answers.
*   **Versatile Question Handling**: Supports common Google Form question types:
    *   Short Answer / Paragraph Text
    *   Multiple Choice
    *   Dropdowns
    *   Checkboxes (currently selects one best option based on AI or email confirmation)
*   **User Data Integration**: Reads user information from a local `userdata.txt` file to personalize responses.
*   **Smart Email Confirmation**: Can automatically tick checkbox options that confirm the user's primary email if it matches the one in `userdata.txt`.
*   **Optimist Mode**: If `optimist: true` is set in `userdata.txt`, the script will automatically select the highest possible rating for rating-based questions.
*   **Pre-filled URL Generation**: Creates a URL that opens the Google Form with answers pre-filled for review.
*   **Interactive Confirmation**: Asks for user confirmation before generating and opening the pre-filled link.

## How it Works (High-Level)

1.  **Input**: Takes a Google Form URL from the user.
2.  **Fetch & Parse**: Downloads the HTML source of the form and extracts the `FB_PUBLIC_LOAD_DATA_` JavaScript variable, which contains the form's structure and questions.
3.  **Question Extraction**: Parses this data to identify each question's text, ID, type, and options (if any).
4.  **User Data Context**: Reads the `userdata.txt` file to get the user's personal information.
5.  **AI Answer Generation**: For each question:
    *   Checks for special handling (email confirmation, optimist rating override).
    *   If not specially handled, constructs a prompt for the Gemini AI, including the question and the full content of `userdata.txt` as context.
    *   Sends the prompt to the Gemini API and receives the generated answer.
    *   Cleans and formats the AI's response.
6.  **Review & Pre-fill**: Displays all generated answers for user review. If confirmed, constructs a pre-filled Google Form URL.
7.  **Browser Launch**: Opens the pre-filled URL in the user's default web browser.

## Setup and Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git
    cd YOUR_REPOSITORY_NAME
    ```
    (Replace `YOUR_USERNAME/YOUR_REPOSITORY_NAME` with your actual GitHub path after you create the public repo.)

2.  **Python Version:**
    This script is tested with Python 3.9+. Ensure you have a compatible Python version installed.

3.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Set Google API Key:**
    You need a Google API key for the Gemini AI. You can get one from [Google AI Studio](https://makersuite.google.com/app/apikey).
    Set it as an environment variable:
    ```bash
    export GOOGLE_API_KEY='YOUR_ACTUAL_GEMINI_API_KEY'
    ```
    (On Windows, use `set GOOGLE_API_KEY=YOUR_ACTUAL_GEMINI_API_KEY` for the current session, or set it permanently via System Properties.)

6.  **Create `userdata.txt`:**
    This file stores your personal information that the AI will use to fill forms. 
    Create a file named `userdata.txt` in the project root directory.
    You can use the following template (copy and paste, then fill with your details):

    ```text
    Name - Your Full Name
    email - your.primary.email@example.com
    phone number = 1234567890
    Address = 123 Main Street, Your City, Your State, Your Country
    Pincode = 12345
    # Add any other relevant personal details, one per line, using a similar format (Key - Value)
    # Example: college name = My University
    # Example: iit bhu (btech) roll number = Your Roll Number
    
    # To enable optimist mode for rating questions, add the following line exactly:
    # optimist: true
    ```
    **Important:** This `userdata.txt` file is ignored by Git (as per `.gitignore`) and will NOT be uploaded to GitHub.

## Usage

1.  Ensure your virtual environment is activated and your `GOOGLE_API_KEY` is set.
2.  Run the script from the project's root directory:
    ```bash
    python Formurl.py
    ```
3.  The script will prompt you to enter the Google Form URL.
4.  It will then process the form, display the questions found, generate answers using AI, and show them for your review.
5.  If you confirm, it will open the pre-filled form in your browser.

## Configuration (`userdata.txt`)

*   **Format**: Try to use a `Key - Value` or `Key = Value` format per line for best results, as the entire content is passed to the AI as context.
*   **`optimist: true`**: Add this exact line to your `userdata.txt` if you want the AI to always pick the highest option for questions that appear to be rating scales.
*   **Primary Email**: For the automatic email confirmation feature, ensure your main email is clearly identifiable (e.g., a line starting with `email - ...`).

## Limitations

*   **Public Forms Only**: The script currently works best with publicly accessible Google Forms. Forms restricted to specific organizations or requiring a login that the script cannot perform will likely result in an error (e.g., 401 Unauthorized), as the script does not handle OAuth 2.0 for authenticated access.
*   **Form Structure Variability**: Google Forms can have varied internal structures. While the script tries to be robust, extremely complex or non-standard forms might not parse correctly. The parsing of `FB_PUBLIC_LOAD_DATA_` can be fragile.
*   **AI Interpretation**: The quality of AI-generated answers depends on the clarity of the form questions, the quality of data in `userdata.txt`, and the capabilities of the Gemini model. Sometimes, AI answers might need manual correction in the review step.
*   **Checkbox Multi-Select**: For checkbox questions that allow multiple selections, the current AI logic typically tries to pick the single best option or the one matching an email confirmation. True multi-select based on AI understanding is not yet implemented.

## Future Ideas / To-Do

*   [ ] Implement OAuth 2.0 to support forms requiring organizational login.
*   [ ] Add more sophisticated handling for multi-select checkbox questions.
*   [ ] Explore using the official Google Forms API (if feasible for this use case and provides better stability than HTML scraping).
*   [ ] Develop a simple GUI interface (e.g., using Tkinter, PyQt, or a web framework like Flask/Streamlit).
*   [ ] Allow for multiple user profiles in `userdata.txt`.
*   [ ] Improve error handling and robustness for various form structures.

## License

(Consider adding a license here, e.g., MIT License. If you do, create a `LICENSE` file as well.)

```
This is an example for an MIT License. If you choose this, create a `LICENSE` file with the MIT License text:

```text
MIT License

Copyright (c) [Year] [Your Name or GitHub Username]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

*This project is for educational and personal convenience purposes. Always ensure you are complying with the terms of service of Google Forms and respecting data privacy when using such tools.* 