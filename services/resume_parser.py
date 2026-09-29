import io
from typing import Dict, Any, Tuple
from services.ai import get_ai_provider

def extract_text_from_file(file_obj, filename: str) -> str:
    """
    Extracts text from PDF, DOCX, or TXT file uploads.
    """
    filename_lower = filename.lower()
    text = ""

    if filename_lower.endswith('.pdf'):
        try:
            import pypdf
            reader = pypdf.PdfReader(file_obj)
            pages_text = [page.extract_text() or '' for page in reader.pages]
            text = "\n".join(pages_text)
        except Exception:
            file_obj.seek(0)
            text = file_obj.read().decode('utf-8', errors='ignore')

    elif filename_lower.endswith('.docx'):
        try:
            import docx
            doc = docx.Document(file_obj)
            text = "\n".join([p.text for p in doc.paragraphs])
        except Exception:
            file_obj.seek(0)
            text = file_obj.read().decode('utf-8', errors='ignore')

    else:
        # Default text read
        try:
            text = file_obj.read().decode('utf-8')
        except Exception:
            file_obj.seek(0)
            text = file_obj.read().decode('latin-1', errors='ignore')

    return text.strip()

def process_and_analyze_resume(file_obj, filename: str) -> Tuple[str, Dict[str, Any]]:
    """
    Reads the file, extracts raw text, and runs the AI/NLP resume analyzer.
    Returns (raw_text, parsed_results_dict).
    """
    raw_text = extract_text_from_file(file_obj, filename)
    ai_provider = get_ai_provider()
    analysis = ai_provider.parse_resume(raw_text)
    return raw_text, analysis
