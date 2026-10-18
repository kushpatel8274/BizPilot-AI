
# BizPilot AI

BizPilot AI is a local AI-assisted business productivity application built with Python and Streamlit.

## Features

- Generate freelance proposals, emails, quotations and payment reminders
- Review and approve drafts before saving
- Import and review retail inventory CSV files
- Calculate profit, profit margin, invoice totals and stock value
- Review saved drafts
- Use a local AI model through Ollama

## Requirements

- Windows
- Python
- Git
- Ollama with a compatible model
- Python dependencies listed in `requirements.txt`

## Setup

1. Clone this repository.
2. Create and activate a Python virtual environment.
3. Install the project dependencies.
4. Install and start Ollama, then download a compatible model.
5. Run the application with Streamlit.

Example commands in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m streamlit run app.py
```

Configure the Ollama model and connection using the application's supported settings.

## Data and privacy

The application stores local business data in SQLite. Do not commit databases,
customer information, credentials or other confidential data to GitHub.

## Development

Run the tests with:

```powershell
python -m pytest
```