# File structure:
# - app.py - Main application file
# - utils/
#   - claude_api.py - Claude API integration
#   - perplexity_api.py - Perplexity API integration
#   - pdf_utils.py - PDF processing utilities
# - components/
#   - sidebar.py - Sidebar navigation component
#   - document_viewer.py - PDF viewer component
#   - clinician_prompts.py - Chat interface for clinicians
#   - note_generator.py - Clinical note generation utilities
#   - patient_context.py - Patient context display
# - data/
#   - sample_data.py - Sample patient and guideline data
# - requirements.txt - Project dependencies

# =====================================
# app.py
# =====================================
import streamlit as st
import os
from PIL import Image
import base64
from datetime import datetime

from components.sidebar import render_sidebar
from components.document_viewer import render_document_viewer
from components.clinician_prompts import render_clinician_prompts
from components.note_generator import render_note_generator
from components.patient_context import render_patient_context
from data.sample_data import get_sample_patient

# Set page configuration
st.set_page_config(
    page_title="EHR Guidelines Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables if they don't exist
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'
if 'selected_guideline' not in st.session_state:
    st.session_state.selected_guideline = None
if 'current_patient' not in st.session_state:
    st.session_state.current_patient = get_sample_patient('diabetes')
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'search_results' not in st.session_state:
    st.session_state.search_results = []

# Apply custom CSS
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stApp {
        background-color: #f8fafc;
    }
    .patient-banner {
        background-color: #eff6ff;
        border: 1px solid #dbeafe;
        border-radius: 0.5rem;
        padding: 0.75rem;
        margin-bottom: 1rem;
    }
    .document-viewer {
        background-color: white;
        border: 1px solid #e2e8f0;
        border-radius: 0.5rem;
        padding: 1rem;
        height: calc(100vh - 10rem);
        overflow-y: auto;
    }
    .chat-message {
        padding: 0.75rem;
        border-radius: 0.5rem;
        margin-bottom: 0.75rem;
        max-width: 80%;
    }
    .user-message {
        background-color: #3b82f6;
        color: white;
        margin-left: auto;
    }
    .assistant-message {
        background-color: #f1f5f9;
        border: 1px solid #e2e8f0;
    }
    .system-message {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        color: #64748b;
    }
    .note-container {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 0.5rem;
        padding: 1rem;
        font-family: monospace;
        white-space: pre-wrap;
    }
    .guideline-reference {
        background-color: #eff6ff;
        border-left: 4px solid #60a5fa;
        padding: 0.75rem;
        margin-top: 0.75rem;
        border-radius: 0 0.25rem 0.25rem 0;
    }
    .footer {
        position: fixed;
        bottom: 0;
        right: 0;
        padding: 0.5rem;
        font-size: 0.8rem;
        color: #94a3b8;
    }
</style>
""", unsafe_allow_html=True)

# Render patient context banner
render_patient_context(st.session_state.current_patient)

# Render sidebar navigation
render_sidebar()

# Render main content based on current page
if st.session_state.current_page == 'home':
    if st.session_state.selected_guideline:
        render_document_viewer(st.session_state.selected_guideline, st.session_state.current_patient)
    else:
        st.markdown("""
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 70vh;">
            <div style="font-size: 4rem; color: #cbd5e1; margin-bottom: 1rem;">📚</div>
            <h2 style="color: #334155; margin-bottom: 0.5rem;">Welcome to MedGuide</h2>
            <p style="color: #64748b; text-align: center; max-width: 400px;">
                Select a guideline document from the sidebar or search for specific clinical recommendations.
            </p>
        </div>
        """, unsafe_allow_html=True)
elif st.session_state.current_page == 'prompts':
    render_clinician_prompts()
elif st.session_state.current_page == 'note':
    render_note_generator('diabetes')
elif st.session_state.current_page == 'her2_note':
    render_note_generator('her2')

# Footer
st.markdown("""
<div class="footer">
    Powered by Claude 3 Sonnet
</div>
""", unsafe_allow_html=True)

# =====================================
# utils/claude_api.py
# =====================================
import requests
import json
import os
from typing import Dict, List, Any, Optional, Union
import time

class ClaudeAPI:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("CLAUDE_API_KEY", "demo_key")
        self.base_url = "https://api.anthropic.com/v1"
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
    
    def query_guidelines(
        self, 
        query: str, 
        patient_context: Dict[str, Any], 
        document_text: Optional[str] = None,
        document_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Query the Claude API for guideline recommendations based on patient context
        """
        # For demo purposes, return mock data if using demo key
        if self.api_key == "demo_key":
            return self._get_mock_guideline_response(query, patient_context)
        
        # Prepare prompt with document content if available
        prompt = f"""
        Patient Context:
        {json.dumps(patient_context, indent=2)}
        
        Query: {query}
        """
        
        if document_text:
            prompt += f"\n\nDocument Text:\n{document_text}\n"
            
        prompt += """
        Please identify specific guideline recommendations relevant to this patient.
        Return the response in JSON format with page numbers and exact text excerpts.
        Format your response as a JSON object with the following structure:
        {
            "recommendations": [
                {
                    "text": "The relevant recommendation text",
                    "explanation": "Why this is relevant for this patient",
                    "page": 42,
                    "source": "ADA Guidelines 2024",
                    "confidence": 0.95
                }
            ]
        }
        """
        
        # Make API call to Claude
        try:
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json={
                    "model": "claude-3-sonnet-20240229",
                    "max_tokens": 1024,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            # Extract and parse JSON from the response
            try:
                content = result["content"][0]["text"]
                # Find JSON content within the response
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    return json.loads(json_str)
                else:
                    # Fallback if structured JSON not found
                    return {"recommendations": [{"text": content, "page": None, "source": None, "confidence": 0.7}]}
            except (KeyError, json.JSONDecodeError):
                return {"recommendations": [{"text": "Unable to parse response", "page": None, "source": None, "confidence": 0}]}
                
        except requests.RequestException as e:
            print(f"API request error: {e}")
            return {"recommendations": []}
    
    def generate_clinical_note(
        self, 
        patient_data: Dict[str, Any], 
        condition: str
    ) -> Dict[str, Any]:
        """
        Generate a clinical note for the specified patient and condition
        """
        # For demo purposes, return mock data if using demo key
        if self.api_key == "demo_key":
            return self._get_mock_note_response(condition, patient_data)
            
        # Prepare prompt
        prompt = f"""
        Generate a succinct assessment and plan for a clinical note based on the following:

        Patient Context:
        {json.dumps(patient_data, indent=2)}

        Condition: {condition}

        Requirements:
        1. Create a structured assessment summarizing patient's current status
        2. Provide a plan organized by problem
        3. Include specific guideline references with page numbers
        4. Keep it concise and formatted for direct inclusion in EHR
        
        Format the note with clear sections for ASSESSMENT and PLAN.
        The note should be ready to copy and paste into an EHR system.
        """
        
        # Make API call to Claude
        try:
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json={
                    "model": "claude-3-sonnet-20240229",
                    "max_tokens": 2048,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            # Extract content
            content = result["content"][0]["text"]
            
            return {
                "title": f"Assessment & Plan for {condition.upper()}",
                "content": content.strip()
            }
                
        except requests.RequestException as e:
            print(f"API request error: {e}")
            return {
                "title": "Error Generating Note",
                "content": "Unable to generate a clinical note at this time."
            }
    
    def process_pdf(self, pdf_content: bytes) -> Dict[str, Any]:
        """
        Process PDF content using Claude's vision capabilities
        """
        # For demo purposes with demo key
        if self.api_key == "demo_key":
            return {
                "title": "Processed PDF",
                "text": "This is a mock processed PDF content for demonstration purposes.",
                "pages": {
                    "1": "Page 1 content would appear here...",
                    "2": "Page 2 content would appear here..."
                },
                "toc": [
                    {"title": "Introduction", "page": 1},
                    {"title": "Recommendations", "page": 2}
                ]
            }
        
        # In a real implementation, this would encode the PDF as base64
        # and send it to Claude's API for analysis
        
        # Placeholder for PDF processing with Claude
        return {
            "title": "Processed PDF",
            "text": "PDF processing would happen here with Claude's vision capabilities",
            "pages": {},
            "toc": []
        }
    
    def _get_mock_guideline_response(self, query: str, patient_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock guideline response for demonstration purposes"""
        time.sleep(1)  # Simulate API delay
        
        if "diabetes" in patient_context.get("diagnosis", "").lower():
            return {
                "recommendations": [
                    {
                        "text": "For patients with Type 2 diabetes with HbA1c levels > 8.0%, clinicians should consider intensifying pharmacologic therapy, adding additional agents, or referral to a specialist.",
                        "explanation": f"The patient's HbA1c is {patient_context.get('recentLabs', {}).get('HbA1c', '8.2%')}, which is above the threshold where guidelines recommend treatment intensification.",
                        "page": 42,
                        "source": "ADA Standards of Medical Care in Diabetes—2024",
                        "confidence": 0.95
                    },
                    {
                        "text": "Target BP should be <140/90 mmHg for most patients with diabetes and hypertension.",
                        "explanation": f"The patient's current BP is {patient_context.get('recentLabs', {}).get('BP', '142/88')}, which is above the recommended target for patients with diabetes.",
                        "page": 18,
                        "source": "JNC 8 Guidelines",
                        "confidence": 0.90
                    }
                ]
            }
        elif "her2" in query.lower() or "breast cancer" in query.lower():
            return {
                "recommendations": [
                    {
                        "text": "Preferred neoadjuvant regimens for HER2-positive disease include: Doxorubicin/cyclophosphamide (AC) followed by paclitaxel + trastuzumab ± pertuzumab.",
                        "explanation": "The patient has HER2-positive breast cancer that would benefit from neoadjuvant therapy with dual HER2 blockade.",
                        "page": 24,
                        "source": "NCCN Guidelines Version 1.2024, Breast Cancer (BINV-L)",
                        "confidence": 0.95
                    }
                ]
            }
        else:
            return {
                "recommendations": [
                    {
                        "text": "Recommendation based on your search would appear here.",
                        "explanation": "This is a placeholder explanation for demo purposes.",
                        "page": 1,
                        "source": "Medical Guidelines",
                        "confidence": 0.7
                    }
                ]
            }
    
    def _get_mock_note_response(self, condition: str, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock clinical note for demonstration purposes"""
        time.sleep(1.5)  # Simulate API delay
        
        if "diabetes" in condition.lower():
            content = f"""ASSESSMENT:
{patient_data.get('age', 54)}yo {patient_data.get('gender', 'male')} with poorly-controlled Type 2 Diabetes (A1c {patient_data.get('recentLabs', {}).get('HbA1c', '8.2%')}) and Hypertension (BP {patient_data.get('recentLabs', {}).get('BP', '142/88')}), with elevated LDL ({patient_data.get('recentLabs', {}).get('LDL', '138mg/dL')}).

PLAN:
1. Diabetes Management:
   - Intensify glycemic control (HbA1c > 8.0% requires therapy adjustment per ADA 2024 Guidelines, p.42)
   - Consider adding second-line agent or adjusting current medication dose
   - Reinforce dietary modifications and physical activity
   - Schedule follow-up A1c check in 3 months

2. Hypertension Management:
   - Target BP < 140/90 mmHg per JNC 8 Guidelines for diabetic patients
   - Continue current antihypertensive; reassess in 4 weeks
   - Encourage sodium restriction and DASH diet

3. Lipid Management:
   - Initiate moderate-intensity statin therapy (LDL > 130mg/dL with diabetes indicates statin benefit per AHA/ACC Guidelines)
   - Baseline liver function tests prior to starting

4. Monitoring:
   - Renal function panel and urine microalbumin
   - Comprehensive foot exam
   - Schedule eye examination if not done within past year"""
            
            return {
                "title": "Assessment & Plan for Diabetes Management",
                "content": content
            }
        
        elif "her2" in condition.lower() or "breast" in condition.lower():
            content = f"""ASSESSMENT:
{patient_data.get('age', 47)}yo {patient_data.get('gender', 'female')} with newly diagnosed left breast invasive ductal carcinoma, {patient_data.get('stage', 'cT2N1M0 stage IIB')}, ER {patient_data.get('receptorStatus', {}).get('ER', '15%')}, PR {patient_data.get('receptorStatus', {}).get('PR', '5%')}, HER2 {patient_data.get('receptorStatus', {}).get('HER2', '3+ by IHC (confirmed by FISH with HER2/CEP17 ratio 5.2)')}.

PLAN:
1. Neoadjuvant Systemic Therapy:
   - Dose-dense AC-T regimen with dual HER2-targeted therapy per NCCN Guidelines v.1.2024 (BINV-L)
   - Regimen details:
     * Dose-dense AC: Doxorubicin 60 mg/m² IV + Cyclophosphamide 600 mg/m² IV q2wks × 4 cycles
     * Followed by: Paclitaxel 80 mg/m² IV weekly × 12 weeks
     * With: Trastuzumab 4 mg/kg IV loading dose, then 2 mg/kg IV weekly
     * And: Pertuzumab 840 mg IV loading dose, then 420 mg IV q3wks

2. Supportive Care:
   - Pegfilgrastim 6 mg SC on day 2 of each AC cycle
   - Antiemetic protocol with AC: Olanzapine 10 mg PO day 1-3, Aprepitant 125 mg PO day 1 then 80 mg days 2-3, Dexamethasone 12 mg IV day 1, Ondansetron 16 mg PO day 1
   - Cardiac monitoring: LVEF assessment at baseline, after AC completion, and q3mo during HER2-targeted therapy (baseline LVEF 62%)
   - Infusion reaction prophylaxis per institutional protocol

3. Monitoring:
   - CBC with diff, CMP prior to each AC cycle and weekly during paclitaxel
   - Clinical tumor assessment prior to each cycle
   - Cardiac monitoring with MUGA scan or echocardiogram at baseline and q3mo
   - Post-treatment imaging with MRI breast to assess response prior to surgery

4. Follow-up:
   - Weekly visits during AC with medical oncology
   - Surgical consultation after cycle 2 of AC to plan for post-neoadjuvant surgery
   - Genetic counseling referral (appointment pending)
   - Consider enrollment in clinical trial NSABP B-60 (pending eligibility screening)"""
            
            return {
                "title": "Assessment & Plan for HER2+ Breast Cancer",
                "content": content
            }
        else:
            return {
                "title": "Assessment & Plan",
                "content": "No specific template available for this condition."
            }

# =====================================
# utils/perplexity_api.py
# =====================================
import requests
import json
import os
from typing import Dict, List, Any, Optional
import time

class PerplexityAPI:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("PERPLEXITY_API_KEY", "demo_key")
        self.base_url = "https://api.perplexity.ai"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def search_web(
        self, 
        query: str, 
        patient_context: Optional[Dict[str, Any]] = None,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search the web for relevant medical information using Perplexity
        """
        # For demo purposes, return mock data if using demo key
        if self.api_key == "demo_key":
            return self._get_mock_search_results(query, patient_context)
        
        # Prepare search query, incorporating patient context if available
        search_query = query
        if patient_context:
            diagnosis = patient_context.get("diagnosis", "")
            if diagnosis:
                search_query += f" for patient with {diagnosis}"
        
        # Medical domains to prioritize
        medical_domains = [
            "guidelines.gov", "nih.gov", "cdc.gov", "who.int", 
            "diabetes.org", "heart.org", "medscape.com", "mayoclinic.org",
            "aafp.org", "nejm.org", "jamanetwork.com", "thelancet.com"
        ]
        
        # Make API call to Perplexity
        try:
            response = requests.post(
                f"{self.base_url}/sonar/search",
                headers=self.headers,
                json={
                    "query": search_query,
                    "source_filter": {"domains": medical_domains},
                    "highlight": True,
                    "max_results": max_results
                },
                timeout=30
            )
            response.raise_for_status()
            results = response.json()
            
            # Process and return results
            processed_results = []
            for result in results:
                processed_results.append({
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                    "url": result.get("url", ""),
                    "source": self._extract_domain(result.get("url", ""))
                })
            
            return processed_results
                
        except requests.RequestException as e:
            print(f"API request error: {e}")
            return []
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain name from URL"""
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            return domain
        except:
            return url
    
    def _get_mock_search_results(self, query: str, patient_context: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate mock search results for demonstration purposes"""
        time.sleep(1)  # Simulate API delay
        
        if "diabetes" in query.lower() or (patient_context and "diabetes" in patient_context.get("diagnosis", "").lower()):
            return [
                {
                    "title": "Standards of Medical Care in Diabetes—2024",
                    "snippet": "The American Diabetes Association's Standards of Medical Care in Diabetes provides clinicians with evidence-based recommendations for managing patients with diabetes and prediabetes.",
                    "url": "https://diabetesjournals.org/care/issue/47/Supplement_1",
                    "source": "diabetesjournals.org"
                },
                {
                    "title": "Treatment Intensification for Patients with Type 2 Diabetes",
                    "snippet": "For patients with HbA1c levels > 8.0%, clinicians should consider adding additional pharmacologic agents or intensifying therapy.",
                    "url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7861057/",
                    "source": "ncbi.nlm.nih.gov"
                },
                {
                    "title": "Guidelines for Hypertension Management in Diabetic Patients",
                    "snippet": "Current recommendations suggest a target blood pressure of <140/90 mmHg for most patients with diabetes, with consideration of lower targets for certain high-risk populations.",
                    "url": "https://www.ahajournals.org/doi/10.1161/HYP.0000000000000065",
                    "source": "ahajournals.org"
                }
            ]
        elif "her2" in query.lower() or "breast cancer" in query.lower():
            return [
                {
                    "title": "NCCN Clinical Practice Guidelines in Oncology: Breast Cancer",
                    "snippet": "Current NCCN guidelines recommend dose-dense AC followed by paclitaxel with HER2-targeted therapy for HER2-positive breast cancer in the neoadjuvant setting.",
                    "url": "https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1419",
                    "source": "nccn.org"
                },
                {
                    "title": "Dual HER2 Blockade in Neoadjuvant Treatment of Breast Cancer",
                    "snippet": "The addition of pertuzumab to trastuzumab-based regimens has been shown to increase the rate of pathologic complete response in neoadjuvant studies.",
                    "url": "https://www.nejm.org/doi/full/10.1056/NEJMoa1306801",
                    "source": "nejm.org"
                }
            ]
        else:
            return [
                {
                    "title": "Medical Guideline Search Results",
                    "snippet": "Search results for medical guidelines would appear here based on your query.",
                    "url": "https://example.com/guidelines",
                    "source": "example.com"
                }
            ]

# =====================================
# utils/pdf_utils.py
# =====================================
import PyPDF2
import io
import os
import base64
from typing import Dict, List, Any, Optional, Tuple
import streamlit as st

def extract_text_from_pdf(pdf_file: io.BytesIO) -> Tuple[str, Dict[int, str]]:
    """
    Extract text from a PDF file
    Returns both full text and text by page
    """
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        full_text = ""
        text_by_page = {}
        
        for i, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            full_text += page_text + "\n\n"
            text_by_page[i+1] = page_text
            
        return full_text, text_by_page
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return "", {}

def get_pdf_page_count(pdf_file: io.BytesIO) -> int:
    """Get the number of pages in a PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        return len(pdf_reader.pages)
    except Exception as e:
        print(f"Error getting PDF page count: {e}")
        return 0

def extract_pdf_metadata(pdf_file: io.BytesIO) -> Dict[str, Any]:
    """Extract metadata from a PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        metadata = pdf_reader.metadata
        if metadata:
            return {
                "title": metadata.get("/Title", ""),
                "author": metadata.get("/Author", ""),
                "subject": metadata.get("/Subject", ""),
                "creator": metadata.get("/Creator", ""),
                "producer": metadata.get("/Producer", ""),
                "creation_date": metadata.get("/CreationDate", ""),
                "modification_date": metadata.get("/ModDate", "")
            }
        return {}
    except Exception as e:
        print(f"Error extracting PDF metadata: {e}")
        return {}

def pdf_to_base64(pdf_file: io.BytesIO) -> str:
    """Convert PDF file to base64 string"""
    pdf_file.seek(0)
    return base64.b64encode(pdf_file.read()).decode('utf-8')

def display_pdf(pdf_file: io.BytesIO, width: int = 700, height: int = 800) -> None:
    """Display a PDF file in Streamlit"""
    base64_pdf = pdf_to_base64(pdf_file)
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="{width}" height="{height}" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def display_pdf_page(pdf_file: io.BytesIO, page_num: int = 1, width: int = 700, height: int = 800) -> None:
    """Display a specific page of a PDF file in Streamlit"""
    try:
        # Create a new PDF with just the specified page
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        pdf_writer = PyPDF2.PdfWriter()
        
        if 1 <= page_num <= len(pdf_reader.pages):
            pdf_writer.add_page(pdf_reader.pages[page_num - 1])
            
            output = io.BytesIO()
            pdf_writer.write(output)
            output.seek(0)
            
            # Display the single page
            base64_pdf = base64.b64encode(output.read()).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="{width}" height="{height}" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
        else:
            st.error(f"Page number {page_num} is out of range. The PDF has {len(pdf_reader.pages)} pages.")
    except Exception as e:
        st.error(f"Error displaying PDF page: {e}")

# =====================================
# components/sidebar.py
# =====================================
import streamlit as st
from data.sample_data import get_sample_guidelines, get_sample_uploaded_docs, get_sample_patient

def render_sidebar():
    with st.sidebar:
        st.markdown("<h1 style='text-align: center; color: #1e40af;'>MedGuide</h1>", unsafe_allow_html=True)
        
        # Navigation
        st.markdown("### Navigation")
        if st.button("📚 Guidelines Home", use_container_width=True):
            st.session_state.current_page = 'home'
            st.session_state.selected_guideline = None
            st.experimental_rerun()
            
        if st.button("💬 Ask Clinical Questions", use_container_width=True):
            st.session_state.current_page = 'prompts'
            st.experimental_rerun()
            
        if st.button("📝 Generate Note (Diabetes)", use_container_width=True):
            st.session_state.current_page = 'note'
            st.session_state.current_patient = get_sample_patient('diabetes')
            st.experimental_rerun()
            
        if st.button("📝 Generate Note (HER2+)", use_container_width=True):
            st.session_state.current_page = 'her2_note'
            st.session_state.current_patient = get_sample_patient('her2')
            st.experimental_rerun()
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Guidelines tabs
        tab1, tab2, tab3 = st.tabs(["Curated", "Uploaded", "Search"])
        
        with tab1:
            st.markdown("#### Curated Guidelines")
            guidelines = get_sample_guidelines()
            
            for guideline in guidelines:
                guideline_container = st.container()
                with guideline_container:
                    if st.button(f"{guideline['title']}", key=f"guideline_{guideline['id']}", use_container_width=True):
                        st.session_state.selected_guideline = guideline
                        st.session_state.current_page = 'home'
                        st.experimental_rerun()
                    st.caption(f"{guideline['source']} • Updated {guideline['lastUpdated']}")
                st.markdown("<hr>", unsafe_allow_html=True)
        
        with tab2:
            st.markdown("#### Uploaded Documents")
            
            # Upload new document
            uploaded_file = st.file_uploader("Upload a guideline PDF", type="pdf")
            if uploaded_file:
                st.success("File uploaded successfully!")
                # In a real app, process and store the file
            
            # Existing uploaded docs
            uploaded_docs = get_sample_uploaded_docs()
            for doc in uploaded_docs:
                doc_container = st.container()
                with doc_container:
                    if st.button(f"{doc['title']}", key=f"doc_{doc['id']}", use_container_width=True):
                        st.session_state.selected_guideline = doc
                        st.session_state.current_page = 'home'
                        st.experimental_rerun()
                    st.caption(f"Uploaded by {doc['uploadedBy']} • {doc['uploadDate']}")
                st.markdown("<hr>", unsafe_allow_html=True)
        
        with tab3:
            st.markdown("#### Search Medical Guidelines")
            
            search_query = st.text_input("Search guidelines", placeholder="Enter search terms...")
            if st.button("Search", use_container_width=True):
                if search_query:
                    st.session_state.search_results = [
                        {
                            "title": "Search Results for Medical Guidelines",
                            "snippet": f"Results for: {search_query}",
                            "url": "#",
                            "source": "Search Engine"
                        }
                    ]
                    # In a real app, perform actual search
            
            # Recent searches
            st.markdown("#### Recent Searches")
            recent_searches = [
                "diabetes medication adjustment when HbA1c > 8%",
                "hypertension treatment in patients with diabetes",
                "statin recommendations for diabetic patients"
            ]
            
            for search in recent_searches:
                if st.button(f"🕒 {search}", key=f"search_{search}", use_container_width=True):
                    # Set search query and perform search
                    pass
        
        # Settings and help
        st.markdown("<hr>", unsafe_allow_html=True)
        
        with st.expander("Settings"):
            st.markdown("### API Configuration")
            claude_api_key = st.text_input("Claude API Key", 
                                          value=st.session_state.get('claude_api_key', ''), 
                                          type="password",
                                          placeholder="Enter Claude API key")
            
            perplexity_api_key = st.text_input("Perplexity API Key", 
                                              value=st.session_state.get('perplexity_api_key', ''), 
                                              type="password",
                                              placeholder="Enter Perplexity API key")
            
            if st.button("Save API Keys"):
                st.session_state.claude_api_key = claude_api_key
                st.session_state.perplexity_api_key = perplexity_api_key
                st.success("API keys saved successfully!")
        
        with st.expander("Help"):
            st.markdown("""
            ### Using MedGuide
            
            - **Guidelines Home**: Browse and view medical guidelines
            - **Ask Clinical Questions**: Chat with AI about patient-specific recommendations
            - **Generate Note**: Create clinical notes for documentation
            
            For more help, please contact support@medguide.example.com
            """)

# =====================================
# components/document_viewer.py
# =====================================
import streamlit as st
import io
import os
from utils.claude_api import ClaudeAPI
from utils.pdf_utils import display_pdf, display_pdf_page
from data.sample_data import get_guideline_content

def render_document_viewer(guideline, patient):
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"## {guideline['title']}")
        st.markdown(f"<p style='color: #64748b;'>{guideline['source']} • Last updated: {guideline['lastUpdated']}</p>", unsafe_allow_html=True)
        
        # Mock document content (in a real app, this would be a PDF viewer)
        content = get_guideline_content(guideline['id'])
        
        # Page navigation
        page_col1, page_col2, page_col3 = st.columns([1, 1, 5])
        with page_col1:
            if st.button("◀ Previous"):
                # Navigate to previous page
                pass
        with page_col2:
            if st.button("Next ▶"):
                # Navigate to next page
                pass
        with page_col3:
            st.markdown(f"<p style='text-align: right;'>Page 42 of 128</p>", unsafe_allow_html=True)
        
        # Document content
        st.markdown("""
        <div class="document-viewer">
            <div style="max-width: 600px; margin: 0 auto;">
                <div style="margin-bottom: 1.5rem;">
                    <h3 style="font-size: 1.25rem; font-weight: bold; text-align: center; margin-bottom: 0.5rem;">Glycemic Targets and Management Guidelines</h3>
                    <h4 style="font-size: 1.125rem; font-weight: 500; text-align: center; color: #64748b; margin-bottom: 1rem;">American Diabetes Association, 2024</h4>
                </div>
                
                <div style="font-size: 0.875rem; line-height: 1.5;">
                    <p style="text-align: justify; margin-bottom: 1rem;">Regular monitoring of glycemia in patients with diabetes is crucial to assess treatment efficacy and reduce risk of hypoglycemia and hyperglycemia. The advent of continuous glucose monitoring (CGM) technology has revolutionized this aspect of diabetes care.</p>
                    
                    <h4 style="font-weight: bold; margin-top: 1rem; margin-bottom: 0.5rem;">Recommendations</h4>
                    
                    <div style="padding: 0.75rem; background-color: #fef9c3; border-left: 4px solid #facc15; margin-bottom: 1rem;">
                        <p><strong>8.1</strong> Most patients with diabetes should be assessed using glycated hemoglobin (HbA1c) testing at least twice per year. <em>(Grade A)</em></p>
                    </div>
                    
                    <div style="padding: 0.75rem; background-color: #dbeafe; border-left: 4px solid #60a5fa; margin-bottom: 1rem;">
                        <p><strong>8.2</strong> When glycemic targets are not being met, quarterly assessments using HbA1c testing are recommended. <em>(Grade B)</em></p>
                    </div>
                    
                    <p style="text-align: justify; margin-bottom: 1rem;">All adult patients with diabetes should have an individualized glycemic target based on their duration of diabetes, age/life expectancy, comorbid conditions, known cardiovascular disease or advanced microvascular complications, hypoglycemia unawareness, and individual patient considerations.</p>
                    
                    <div style="padding: 0.75rem; background-color: #fef9c3; border-left: 4px solid #facc15; margin-bottom: 1rem;">
                        <p><strong>8.5</strong> For patients with Type 2 diabetes with HbA1c levels <strong>&gt; 8.0%</strong>, clinicians should consider intensifying pharmacologic therapy, adding additional agents, or referral to a specialist. <em>(Grade A)</em></p>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### AI Assistant")
        
        # Patient-specific recommendations
        st.markdown("#### Patient-specific Recommendations")
        
        # Get recommendations from Claude API
        claude_api = ClaudeAPI(st.session_state.get('claude_api_key', 'demo_key'))
        recommendations = claude_api.query_guidelines(
            query="relevant recommendations for this patient",
            patient_context=patient,
            document_ids=[guideline['id']]
        ).get('recommendations', [])
        
        for rec in recommendations:
            st.markdown(f"""
            <div style="padding: 0.75rem; background-color: #dbeafe; border-radius: 0.5rem; margin-bottom: 0.75rem; font-size: 0.875rem;">
                <p style="margin-bottom: 0.5rem;">{rec.get('explanation', '')}</p>
                <p style="font-weight: 500;">"{rec.get('text', '')}"</p>
                <p style="font-size: 0.75rem; color: #3b82f6; margin-top: 0.5rem;">Page {rec.get('page', '')}, {rec.get('source', '')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Ask about document
        st.markdown("#### Ask about this document")
        question = st.text_input("Ask a question about this guideline", key="guideline_question")
        if st.button("Ask", key="ask_guideline_button"):
            if question:
                # Query Claude about the document
                pass
        
        # Related guidelines
        st.markdown("#### Related Guidelines")
        
        st.markdown("""
        <div style="padding: 0.5rem; border: 1px solid #e2e8f0; border-radius: 0.375rem; font-size: 0.875rem; margin-bottom: 0.5rem; cursor: pointer; hover:bg-gray-50;">
            <p style="font-weight: 500; color: #3b82f6;">Hypertension Management in Diabetes</p>
            <p style="font-size: 0.75rem; color: #64748b;">JNC 8 Guidelines, p.18-22</p>
        </div>
        
        <div style="padding: 0.5rem; border: 1px solid #e2e8f0; border-radius: 0.375rem; font-size: 0.875rem; cursor: pointer; hover:bg-gray-50;">
            <p style="font-weight: 500; color: #3b82f6;">Medication Adjustments for HbA1c > 8%</p>
            <p style="font-size: 0.75rem; color: #64748b;">ADA Guidelines 2024, p.45-48</p>
        </div>
        """, unsafe_allow_html=True)

# =====================================
# components/clinician_prompts.py
# =====================================
import streamlit as st
import json
import time
from utils.claude_api import ClaudeAPI

def render_clinician_prompts():
    # Initialize chat history if not exists
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = [
            {
                "role": "system",
                "content": "I can help you find relevant guidelines and recommendations for your patient. What would you like to know?"
            }
        ]
    
    # Initialize Claude API
    claude_api = ClaudeAPI(st.session_state.get('claude_api_key', 'demo_key'))
    
    # Current patient context
    patient = st.session_state.current_patient
    
    # Page header
    st.markdown(f"## MedGuide Assistant")
    
    # Display chat messages
    for message in st.session_state.chat_history:
        role = message.get("role", "user")
        content = message.get("content", "")
        is_note = message.get("is_note", False)
        note = message.get("note", None)
        source = message.get("source", None)
        
        if role == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                {content}
            </div>
            """, unsafe_allow_html=True)
        elif role == "system":
            st.markdown(f"""
            <div class="chat-message system-message">
                {content}
            </div>
            """, unsafe_allow_html=True)
        else:  # assistant
            if is_note and note:
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <p>{content}</p>
                    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 0.5rem; padding: 1rem; margin-top: 0.75rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                            <div style="display: flex; align-items: center;">
                                <span style="margin-right: 0.25rem;">📄</span>
                                <span style="font-weight: 500; color: #334155;">{note.get("title", "Clinical Note")}</span>
                            </div>
                            <button id="copy-button" 
                                onclick="navigator.clipboard.writeText(`{note.get('content', '')}`.replace(/\\n/g, '\\n')); 
                                document.getElementById('copy-button').innerHTML = '✓ Copied!'; 
                                setTimeout(() => document.getElementById('copy-button').innerHTML = '📋 Copy', 2000);"
                                style="background-color: #eff6ff; color: #3b82f6; border: none; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; cursor: pointer;">
                                📋 Copy
                            </button>
                        </div>
                        <pre style="background-color: white; border: 1px solid #e2e8f0; padding: 0.5rem; border-radius: 0.25rem; font-family: monospace; font-size: 0.75rem; white-space: pre-wrap; overflow-x: auto;">{note.get("content", "")}</pre>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                source_html = ""
                if source:
                    source_html = f"""
                    <div style="display: flex; align-items: center; margin-top: 0.5rem; padding: 0.25rem 0.5rem; background-color: #3b82f6; color: white; border-radius: 0.25rem; font-size: 0.75rem; width: fit-content;">
                        <span style="margin-right: 0.25rem;">📚</span>
                        <span>{source}</span>
                    </div>
                    """
                
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <p>{content}</p>
                    {source_html}
                </div>
                """, unsafe_allow_html=True)

    # Display suggested prompts in two columns
    if len(st.session_state.chat_history) < 2:  # Only show if chat just started
        st.markdown("### Suggested for this patient")
        
        suggested_prompts = [
            "What medication adjustments are recommended for HbA1c > 8%?",
            "What BP targets should I aim for with this diabetic patient?",
            "When should I consider adding a statin given the patient's LDL?",
            "Generate a succinct assessment and plan for my note",
            "What monitoring frequency is recommended for this patient?",
            "Are there any drug interactions I should be aware of?"
        ]
        
        col1, col2 = st.columns(2)
        with col1:
            for i in range(0, len(suggested_prompts), 2):
                if i < len(suggested_prompts):
                    if st.button(suggested_prompts[i], key=f"suggest_{i}", use_container_width=True):
                        handle_user_input(suggested_prompts[i], claude_api, patient)
        with col2:
            for i in range(1, len(suggested_prompts), 2):
                if i < len(suggested_prompts):
                    if st.button(suggested_prompts[i], key=f"suggest_{i}", use_container_width=True):
                        handle_user_input(suggested_prompts[i], claude_api, patient)
    
    # Input for new message
    user_input = st.text_input("Ask about guidelines or recommendations", key="user_input")
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("Send", use_container_width=True) or (user_input and user_input != st.session_state.get('last_input', '')):
            if user_input:
                st.session_state['last_input'] = user_input
                handle_user_input(user_input, claude_api, patient)

def handle_user_input(user_input, claude_api, patient):
    # Add user message to chat history
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_input
    })
    
    # Show thinking indicator
    with st.spinner("AI is thinking..."):
        # Check if the user is asking for a note
        if "assessment" in user_input.lower() and "plan" in user_input.lower() and "note" in user_input.lower():
            # Generate clinical note
            response = claude_api.generate_clinical_note(patient, "diabetes" if "diabetes" in patient["diagnosis"].lower() else "general")
            
            # Add assistant response with note
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "I've prepared an assessment and plan based on this patient's information and relevant guidelines:",
                "is_note": True,
                "note": {
                    "title": response.get("title", "Clinical Note"),
                    "content": response.get("content", "")
                }
            })
        else:
            # Query guidelines
            response = claude_api.query_guidelines(user_input, patient)
            recommendations = response.get("recommendations", [])
            
            if recommendations:
                rec = recommendations[0]  # Get first recommendation
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"{rec.get('explanation', '')}\n\n\"{rec.get('text', '')}\"",
                    "source": f"{rec.get('source', '')}, page {rec.get('page', '')}"
                })
            else:
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": "I couldn't find specific guideline recommendations for your query. Please try asking a different question or provide more context."
                })
    
    # Rerun to update the UI
    st.experimental_rerun()

# =====================================
# components/note_generator.py
# =====================================
import streamlit as st
import json
import time
from utils.claude_api import ClaudeAPI

def render_note_generator(condition_type="diabetes"):
    # Initialize Claude API
    claude_api = ClaudeAPI(st.session_state.get('claude_api_key', 'demo_key'))
    
    # Current patient context
    patient = st.session_state.current_patient
    
    # Set theme based on condition type
    if condition_type == "her2":
        theme_color = "#db2777"  # pink-600
        theme_light = "#fce7f3"  # pink-100
        theme_title = "HER2+ Breast Cancer Treatment Plan"
        theme_subtitle = "Neoadjuvant regimen with guideline references for dose-dense AC-T with dual HER2 blockade"
    else:
        theme_color = "#2563eb"  # blue-600
        theme_light = "#dbeafe"  # blue-100
        theme_title = "Assessment & Plan Generator"
        theme_subtitle = "Generates clinically relevant notes based on patient data and current guidelines"
    
    # Page header
    st.markdown(f"""
    <div style="background-color: {theme_color}; padding: 1rem; border-radius: 0.5rem 0.5rem 0 0; color: white;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="display: flex; align-items: center;">
                <span style="margin-right: 0.5rem; font-size: 1.25rem;">📄</span>
                <h2 style="font-weight: 600; font-size: 1.25rem; margin: 0;">{theme_title}</h2>
            </div>
            <span style="font-size: 0.75rem; background-color: rgba(255,255,255,0.2); padding: 0.25rem 0.5rem; border-radius: 0.25rem;">Guideline-Informed</span>
        </div>
        <p style="margin-top: 0.25rem; font-size: 0.875rem; color: rgba(255,255,255,0.8);">
            {theme_subtitle}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Patient context banner
    st.markdown(f"""
    <div style="background-color: {theme_light}; padding: 0.75rem; border-bottom: 1px solid rgba(0,0,0,0.1);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 0.875rem; font-weight: 500; color: {theme_color};">{patient['name']}, {patient['age']}</span>
                <span style="font-size: 0.75rem; color: {theme_color}; margin-left: 0.5rem;">{patient['diagnosis']}</span>
            </div>
            <div style="font-size: 0.75rem; color: {theme_color};">
                {get_patient_labs_string(patient)}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Main content
    st.markdown("""
    <div style="background-color: white; padding: 1rem; border: 1px solid #e2e8f0; border-radius: 0 0 0.5rem 0.5rem;">
    """, unsafe_allow_html=True)
    
    # Note title and actions
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
        <div style="display: flex; align-items: center;">
            <span style="margin-right: 0.5rem; color: {theme_color};">📄</span>
            <h3 style="font-weight: 500; color: #334155; margin: 0;">Generated Assessment & Plan</h3>
        </div>
        """, unsafe_allow_html=True)
    
    # Generate note if it doesn't exist in session state
    if 'current_note' not in st.session_state or st.session_state.get('current_note_type') != condition_type:
        with st.spinner("Generating clinical note..."):
            response = claude_api.generate_clinical_note(patient, condition_type)
            st.session_state.current_note = response.get("content", "Error generating note")
            st.session_state.current_note_type = condition_type
    
    # Display note content
    note_container = st.container()
    with note_container:
        # Editing and copying options
        edit_col, copy_col = st.columns([1, 1])
        
        with edit_col:
            if 'note_editing' not in st.session_state:
                st.session_state.note_editing = False
            
            if st.button("✏️ Edit Note" if not st.session_state.note_editing else "Cancel Edit", use_container_width=True):
                st.session_state.note_editing = not st.session_state.note_editing
        
        with copy_col:
            if st.button("📋 Copy to Clipboard", use_container_width=True):
                st.write(f'<div id="copy-trigger" data-content="{st.session_state.current_note.replace(chr(10), "\\n").replace(chr(13), "\\r")}" style="display:none"></div>', unsafe_allow_html=True)
                st.markdown("""
                <script>
                    // Wait for the copy-trigger element to appear
                    const checkExist = setInterval(function() {
                        const copyTrigger = document.getElementById('copy-trigger');
                        if (copyTrigger) {
                            clearInterval(checkExist);
                            const content = copyTrigger.getAttribute('data-content');
                            navigator.clipboard.writeText(content);
                            
                            // Show success message
                            const copyButton = document.querySelector("button:contains('Copy to Clipboard')");
                            if (copyButton) {
                                copyButton.innerText = "✓ Copied!";
                                setTimeout(() => copyButton.innerText = "📋 Copy to Clipboard", 2000);
                            }
                        }
                    }, 100);
                </script>
                """, unsafe_allow_html=True)
        
        # Note content
        if st.session_state.note_editing:
            edited_note = st.text_area("Edit Note", st.session_state.current_note, height=400)
            save_col, _ = st.columns([1, 3])
            with save_col:
                if st.button("💾 Save Changes", use_container_width=True):
                    st.session_state.current_note = edited_note
                    st.session_state.note_editing = False
                    st.experimental_rerun()
        else:
            st.markdown("""
            <div class="note-container">
            """, unsafe_allow_html=True)
            
            # Format the note with proper line breaks
            formatted_note = st.session_state.current_note.replace("\n", "<br>")
            st.markdown(f"<div>{formatted_note}</div>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Clinical considerations for HER2+ breast cancer
        if condition_type == "her2":
            st.markdown("""
            <div style="margin-top: 1rem; padding: 0.75rem; background-color: #fef9c3; border-left: 4px solid #facc15; border-radius: 0 0.25rem 0.25rem 0; display: flex;">
                <span style="color: #ca8a04; margin-right: 0.5rem; font-size: 1.25rem;">⚠️</span>
                <div style="font-size: 0.875rem;">
                    <p style="font-weight: 500; color: #854d0e; margin-bottom: 0.25rem;">Important Clinical Considerations</p>
                    <ul style="color: #854d0e; margin: 0.25rem 0 0 1.25rem; padding: 0;">
                        <li>Cardiac monitoring is critical - baseline and q3month LVEF assessment</li>
                        <li>Consider dose reduction for paclitaxel in patients with pre-existing neuropathy</li>
                        <li>Primary G-CSF prophylaxis required due to dose-density of regimen</li>
                        <li>Pertuzumab contraindicated if LVEF &lt;50% or pregnancy</li>
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Guideline references
    st.markdown("""
    <h4 style="font-size: 0.875rem; font-weight: 500; color: #475569; margin-top: 1rem; margin-bottom: 0.5rem;">Guideline References</h4>
    """, unsafe_allow_html=True)
    
    if condition_type == "her2":
        st.markdown("""
        <div class="guideline-reference">
            <p style="font-weight: 500; font-size: 0.75rem;">NCCN Guidelines Version 1.2024, Breast Cancer (BINV-L)</p>
            <p style="color: #475569; font-size: 0.75rem; margin-top: 0.25rem;">
                "Preferred neoadjuvant regimens for HER2-positive disease include: Doxorubicin/cyclophosphamide (AC) followed by paclitaxel + trastuzumab ± pertuzumab. The addition of pertuzumab to trastuzumab-based regimens has been shown to increase the rate of pCR in neoadjuvant studies."
            </p>
        </div>
        
        <div class="guideline-reference" style="background-color: #eff6ff; border-left: 4px solid #60a5fa;">
            <p style="font-weight: 500; font-size: 0.75rem;">ASCO Clinical Practice Guideline Update (2018)</p>
            <p style="color: #475569; font-size: 0.75rem; margin-top: 0.25rem;">
                "For patients with advanced HER2-positive breast cancer treated with first-line trastuzumab, pertuzumab, and taxane for 4 to 6 months to maximal response or until limiting toxicity, and whose disease is not progressing at the completion of taxane-based therapy: Clinicians should continue HER2-targeted therapy until time of disease progression or limiting toxicity."
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Evidence section for HER2+
        st.markdown("""
        <h4 style="font-size: 0.875rem; font-weight: 500; color: #475569; margin-top: 1rem; margin-bottom: 0.5rem;">Key Supporting Evidence</h4>
        
        <div style="padding: 0.5rem; border: 1px solid #e2e8f0; border-radius: 0.375rem; margin-bottom: 0.5rem; font-size: 0.75rem;">
            <p style="font-weight: 500;">NEOSPHERE Trial (Lancet Oncol. 2012)</p>
            <p style="color: #475569; margin-top: 0.25rem;">
                Dual HER2 blockade with trastuzumab + pertuzumab improved pCR rate to 45.8% vs 29.0% with trastuzumab alone when combined with docetaxel in the neoadjuvant setting.
            </p>
        </div>
        
        <div style="padding: 0.5rem; border: 1px solid #e2e8f0; border-radius: 0.375rem; font-size: 0.75rem;">
            <p style="font-weight: 500;">BERENICE Trial (Ann Oncol. 2018)</p>
            <p style="color: #475569; margin-top: 0.25rem;">
                Demonstrated the cardiac safety of dose-dense AC followed by weekly paclitaxel with dual HER2 blockade in the neoadjuvant setting. Pathologic complete response was achieved in 61.8% of patients.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="guideline-reference" style="background-color: #fef9c3; border-left: 4px solid #facc15;">
            <p style="font-weight: 500; font-size: 0.75rem;">ADA Standards of Medical Care in Diabetes—2024, p.42</p>
            <p style="color: #475569; font-size: 0.75rem; margin-top: 0.25rem;">
                "For patients with Type 2 diabetes with HbA1c levels > 8.0%, clinicians should consider intensifying pharmacologic therapy, adding additional agents, or referral to a specialist. (Grade A)"
            </p>
        </div>
        
        <div class="guideline-reference" style="background-color: #eff6ff; border-left: 4px solid #60a5fa;">
            <p style="font-weight: 500; font-size: 0.75rem;">JNC 8 Guidelines for Hypertension, p.18</p>
            <p style="color: #475569; font-size: 0.75rem; margin-top: 0.25rem;">
                "In the general nonblack population, including those with diabetes, initial antihypertensive treatment should include a thiazide-type diuretic, calcium channel blocker (CCB), angiotensin-converting enzyme inhibitor (ACEI), or angiotensin receptor blocker (ARB)."
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer
    st.markdown(f"""
    <div style="padding: 0.75rem; border-top: 1px solid #e2e8f0; background-color: #f8fafc; display: flex; justify-content: space-between; align-items: center; margin-top: 1rem;">
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <button style="border: none; background: none; color: #64748b; cursor: pointer;">
                <span>👍</span>
            </button>
            <button style="border: none; background: none; color: #64748b; cursor: pointer;">
                <span>🔖</span>
            </button>
            <button style="border: none; background: none; color: #64748b; cursor: pointer;">
                <span>💾</span>
            </button>
        </div>
        <div style="font-size: 0.75rem; color: #64748b;">
            Generated using Claude 3 Sonnet
        </div>
        <button style="border: none; background: none; color: {theme_color}; font-size: 0.75rem; display: flex; align-items: center; cursor: pointer;">
            <span style="margin-right: 0.25rem;">View Full Guidelines</span>
            <span>→</span>
        </button>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

def get_patient_labs_string(patient):
    labs = patient.get('recentLabs', {})
    labs_strings = []
    for key, value in labs.items():
        labs_strings.append(f"{key}: {value}")
    return ", ".join(labs_strings)

# =====================================
# components/patient_context.py
# =====================================
import streamlit as st

def render_patient_context(patient):
    st.markdown(f"""
    <div class="patient-banner">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h3 style="font-size: 0.875rem; font-weight: 500; margin: 0; color: #1e40af;">{patient['name']}, {patient['age']}</h3>
                <p style="font-size: 0.75rem; margin: 0; color: #3b82f6;">{patient['diagnosis']}</p>
            </div>
            <div style="font-size: 0.75rem; color: #3b82f6;">
                <span style="font-weight: 500;">Recent:</span> {get_patient_labs_string(patient)}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def get_patient_labs_string(patient):
    labs = patient.get('recentLabs', {})
    labs_strings = []
    for key, value in labs.items():
        labs_strings.append(f"{key}: {value}")
    return ", ".join(labs_strings)

# =====================================
# data/sample_data.py
# =====================================
import json
from typing import Dict, List, Any, Optional

def get_sample_guidelines() -> List[Dict[str, Any]]:
    """Return sample guideline data"""
    return [
        {
            "id": "1",
            "title": "Diabetes Management - ADA 2024",
            "source": "American Diabetes Association",
            "lastUpdated": "Jan 2024"
        },
        {
            "id": "2",
            "title": "Hypertension Guidelines - JNC 8",
            "source": "Journal of the American Medical Association",
            "lastUpdated": "Dec 2023"
        },
        {
            "id": "3",
            "title": "Lipid Management in Cardiovascular Disease",
            "source": "American Heart Association",
            "lastUpdated": "Mar 2024"
        },
        {
            "id": "4",
            "title": "HER2+ Breast Cancer - NCCN Guidelines",
            "source": "National Comprehensive Cancer Network",
            "lastUpdated": "Feb 2024"
        }
    ]

def get_sample_uploaded_docs() -> List[Dict[str, Any]]:
    """Return sample uploaded documents"""
    return [
        {
            "id": "uploaded_1",
            "title": "Hospital Diabetes Protocol",
            "source": "Internal Document",
            "uploadedBy": "Dr. Sarah Chen",
            "uploadDate": "Feb 15, 2024",
            "lastUpdated": "Feb 15, 2024"
        },
        {
            "id": "uploaded_2",
            "title": "Cardiology Department BP Management",
            "source": "Internal Document",
            "uploadedBy": "Dr. Michael Johnson",
            "uploadDate": "Jan 22, 2024",
            "lastUpdated": "Jan 22, 2024"
        }
    ]

def get_sample_patient(condition_type: str = "diabetes") -> Dict[str, Any]:
    """Return sample patient data based on condition type"""
    if condition_type == "her2":
        return {
            "id": "p002",
            "name": "Sarah Johnson",
            "age": 47,
            "gender": "female",
            "diagnosis": "Invasive Ductal Carcinoma, HER2+",
            "stage": "cT2N1M0 stage IIB",
            "receptorStatus": {
                "ER": "15%",
                "PR": "5%",
                "HER2": "3+ by IHC (confirmed by FISH with HER2/CEP17 ratio 5.2)"
            },
            "recentLabs": {
                "CBC": "WNL",
                "CMP": "WNL",
                "LVEF": "62%"
            }
        }
    else:  # diabetes or default
        return {
            "id": "p001",
            "name": "James Wilson",
            "age": 54,
            "gender": "male",
            "diagnosis": "Type 2 Diabetes, Hypertension",
            "recentLabs": {
                "HbA1c": "8.2%",
                "BP": "142/88",
                "LDL": "138mg/dL"
            }
        }

def get_guideline_content(guideline_id: str) -> str:
    """Return sample content for a specific guideline"""
    
    # Diabetes content
    if guideline_id == "1":
        return """
# Glycemic Targets and Management Guidelines

Regular monitoring of glycemia in patients with diabetes is crucial to assess treatment efficacy and reduce risk of hypoglycemia and hyperglycemia. The advent of continuous glucose monitoring (CGM) technology has revolutionized this aspect of diabetes care.

## Recommendations

8.1 Most patients with diabetes should be assessed using glycated hemoglobin (HbA1c) testing at least twice per year. (Grade A)

8.2 When glycemic targets are not being met, quarterly assessments using HbA1c testing are recommended. (Grade B)

All adult patients with diabetes should have an individualized glycemic target based on their duration of diabetes, age/life expectancy, comorbid conditions, known cardiovascular disease or advanced microvascular complications, hypoglycemia unawareness, and individual patient considerations.

8.5 For patients with Type 2 diabetes with HbA1c levels > 8.0%, clinicians should consider intensifying pharmacologic therapy, adding additional agents, or referral to a specialist. (Grade A)
        """
    
    # Hypertension content
    elif guideline_id == "2":
        return """
# Hypertension Guidelines - JNC 8

## Recommendations

1. In the general population ≥60 years of age, initiate pharmacologic treatment to lower BP at systolic blood pressure (SBP) ≥150 mm Hg or diastolic blood pressure (DBP) ≥90 mm Hg and treat to a goal SBP <150 mm Hg and goal DBP <90 mm Hg. (Grade A)

2. In the general population <60 years of age, initiate pharmacologic treatment to lower BP at DBP ≥90 mm Hg and treat to a goal DBP <90 mm Hg. (Grade A)

3. In the general population <60 years of age, initiate pharmacologic treatment to lower BP at SBP ≥140 mm Hg and treat to a goal SBP <140 mm Hg. (Grade E)

4. In the population aged ≥18 years with chronic kidney disease (CKD), initiate pharmacologic treatment to lower BP at SBP ≥140 mm Hg or DBP ≥90 mm Hg and treat to goal SBP <140 mm Hg and goal DBP <90 mm Hg. (Grade E)

5. In the population aged ≥18 years with diabetes, initiate pharmacologic treatment to lower BP at SBP ≥140 mm Hg or DBP ≥90 mm Hg and treat to a goal SBP <140 mm Hg and goal DBP <90 mm Hg. (Grade E)
        """
    
    # HER2+ Breast Cancer content
    elif guideline_id == "4":
        return """
# NCCN Guidelines for HER2-Positive Breast Cancer

## Neoadjuvant/Adjuvant Therapy Recommendations

Preferred regimens for HER2-positive disease include:

1. Doxorubicin/cyclophosphamide (AC) followed by paclitaxel + trastuzumab ± pertuzumab
   - AC: Doxorubicin 60 mg/m² IV + Cyclophosphamide 600 mg/m² IV q2-3wks × 4 cycles
   - Followed by: Paclitaxel 80 mg/m² IV weekly × 12 weeks
   - With: Trastuzumab 4 mg/kg IV loading dose, then 2 mg/kg IV weekly
   - And: Pertuzumab 840 mg IV loading dose, then 420 mg IV q3wks (optional)

2. Docetaxel/carboplatin/trastuzumab + pertuzumab (TCH+P)
   - Docetaxel 75 mg/m² IV + Carboplatin AUC 6 IV day 1 q3wks × 6 cycles
   - With: Trastuzumab 8 mg/kg IV loading dose, then 6 mg/kg IV q3wks
   - And: Pertuzumab 840 mg IV loading dose, then 420 mg IV q3wks

The addition of pertuzumab to trastuzumab-based regimens has been shown to increase the rate of pCR in neoadjuvant studies.

Cardiac monitoring:
- LVEF assessment at baseline and q3mo during HER2-targeted therapy
- Hold HER2-targeted therapy for >16% absolute decrease in LVEF from baseline, or LVEF <50%
        """
    
    # Default content
    else:
        return """
# Medical Guideline Content

This is a placeholder for guideline content. In a real application, this would contain the actual text from the selected guideline document.

## Recommendations

1. Recommendation one would appear here.
2. Recommendation two would appear here.
3. Recommendation three would appear here.

## Evidence Quality

The quality of evidence supporting these recommendations is [level].
        """

# =====================================
# requirements.txt
# =====================================
"""
streamlit==1.22.0
PyPDF2==3.0.1
requests==2.31.0
Pillow==9.5.0
python-dotenv==1.0.0
"""

# =====================================
# README.md
# =====================================
"""
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
"""
