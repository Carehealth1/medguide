# MedGuide - EHR Guidelines Application

MedGuide is a Streamlit application that enables clinicians to access and navigate medical guidelines within their EHR system. The application uses Claude API for document analysis and note generation, and Perplexity API for internet searches.

## Features

- View curated guidelines and uploaded documents
- Search for specific recommendations
- Chat with AI to get guideline-based answers for specific patients
- Generate clinical notes based on guidelines
- Patient-specific recommendations

## Setup Instructions

1. Clone this repository
2. Install requirements:
   ```
   pip install -r requirements.txt
   ```
3. Set up your environment variables:
   - Create a `.env` file with the following variables:
     ```
     CLAUDE_API_KEY=your_claude_api_key
     PERPLEXITY_API_KEY=your_perplexity_api_key
     ```
4. Run the app:
   ```
   streamlit run app.py
   ```

## Application Structure

- `app.py` - Main application file
- `utils/` - Utility functions for API integrations and PDF processing
- `components/` - UI components
- `data/` - Sample data and data handling functions

## Requirements

- Python 3.8+
- Streamlit
- PyPDF2
- Requests
- Pillow
- python-dotenv

## Using the Application

1. **Browse Guidelines**: Use the sidebar to browse through curated guidelines or uploaded documents
2. **Ask Questions**: Navigate to the "Ask Clinical Questions" page to chat with the AI about guidelines
3. **Generate Notes**: Use the note generation feature to create clinical notes based on guidelines

## API Keys

To use the full functionality of this application, you'll need:
- An API key from Anthropic (Claude)
- An API key from Perplexity

You can enter these in the Settings section of the sidebar.
