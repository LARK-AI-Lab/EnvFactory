from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class PDFDocument(BaseModel):
    """Represents a generated PDF document."""
    id: str = Field(..., description="Unique identifier for the PDF")
    url: str = Field(..., description="Presigned URL for downloading")
    page_count: int = Field(..., ge=0, description="Number of pages")
    file_size: int = Field(..., ge=0, description="Size in bytes")
    source_type: str = Field(..., description="Source: html, combined, ocr, etc.")
    created_at: str = Field(..., description="Creation timestamp")

class ExportJob(BaseModel):
    """Represents a PDF export operation."""
    id: str = Field(..., description="Unique identifier for the export job")
    source_pdf_id: str = Field(..., description="Source PDF ID")
    target_format: str = Field(..., pattern=r"^(docx|xlsx|pptx|jpeg|png)$", description="Export format")
    export_url: str = Field(..., description="Presigned URL for exported file")
    page_count: int = Field(..., ge=0, description="Number of pages")
    created_at: str = Field(..., description="Creation timestamp")

class OCRJob(BaseModel):
    """Represents an OCR operation result."""
    id: str = Field(..., description="Unique identifier for the OCR job")
    source_pdf_id: str = Field(..., description="Source PDF ID")
    output_type: str = Field(..., pattern=r"^(searchable_pdf|text_extraction)$", description="OCR output type")
    output_url: str = Field(..., description="Presigned URL for output")
    extracted_text: Optional[str] = Field(default=None, description="Extracted text if applicable")
    confidence_score: float = Field(..., ge=0, le=100, description="OCR confidence score")
    created_at: str = Field(..., description="Creation timestamp")

class CombinedPDF(BaseModel):
    """Represents a merged PDF document."""
    id: str = Field(..., description="Unique identifier for the combined PDF")
    url: str = Field(..., description="Presigned URL for downloading")
    source_pdf_ids: List[str] = Field(..., description="List of source PDF IDs")
    total_pages: int = Field(..., ge=0, description="Total pages")
    source_count: int = Field(..., ge=0, description="Number of sources")
    created_at: str = Field(..., description="Creation timestamp")

class Permissions(BaseModel):
    """Permission settings for PDF protection."""
    printing: bool = Field(default=False, description="Allow printing")
    copying: bool = Field(default=False, description="Allow copying")
    editing: bool = Field(default=False, description="Allow editing")
    commenting: bool = Field(default=False, description="Allow commenting")

class ProtectedPDF(BaseModel):
    """Represents a password-protected PDF."""
    id: str = Field(..., description="Unique identifier for the protected PDF")
    source_pdf_id: str = Field(..., description="Source PDF ID")
    url: str = Field(..., description="Presigned URL for downloading")
    encryption_level: str = Field(default="AES-256", description="Encryption standard")
    permissions: Permissions = Field(..., description="Applied permissions")
    created_at: str = Field(..., description="Creation timestamp")

class AdobePDFScenario(BaseModel):
    """Main scenario model for Adobe PDF Services."""
    pdfs: Dict[str, PDFDocument] = Field(default={}, description="Generated PDFs")
    exports: Dict[str, ExportJob] = Field(default={}, description="Export operations")
    ocr_jobs: Dict[str, OCRJob] = Field(default={}, description="OCR operations")
    combined_pdfs: Dict[str, CombinedPDF] = Field(default={}, description="Merged PDFs")
    protected_pdfs: Dict[str, ProtectedPDF] = Field(default={}, description="Protected PDFs")
    current_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Current timestamp ISO 8601")
    pdf_counter: int = Field(default=0, ge=0, description="Counter for generating unique IDs")
    base_url: str = Field(default="https://api.adobe.example.com/pdfs", description="Base URL for generating presigned URLs")

Scenario_Schema = [PDFDocument, ExportJob, OCRJob, CombinedPDF, Permissions, ProtectedPDF, AdobePDFScenario]

# Section 2: Class
class AdobePDFAPI:
    def __init__(self):
        """Initialize Adobe PDF API with empty state."""
        self.pdfs: Dict[str, PDFDocument] = {}
        self.exports: Dict[str, ExportJob] = {}
        self.ocr_jobs: Dict[str, OCRJob] = {}
        self.combined_pdfs: Dict[str, CombinedPDF] = {}
        self.protected_pdfs: Dict[str, ProtectedPDF] = {}
        self.current_time: str = ""
        self.pdf_counter: int = 0
        self.base_url: str = ""

    def load_scenario(self, scenario: dict) -> None:
        """
        Load scenario data into the API instance.
        """
        model = AdobePDFScenario(**scenario)
        self.pdfs = model.pdfs
        self.exports = model.exports
        self.ocr_jobs = model.ocr_jobs
        self.combined_pdfs = model.combined_pdfs
        self.protected_pdfs = model.protected_pdfs
        self.current_time = model.current_time
        self.pdf_counter = model.pdf_counter
        self.base_url = model.base_url

    def save_scenario(self) -> dict:
        """
        Save current state as scenario dictionary.
        """
        return {
            "pdfs": {k: v.model_dump() for k, v in self.pdfs.items()},
            "exports": {k: v.model_dump() for k, v in self.exports.items()},
            "ocr_jobs": {k: v.model_dump() for k, v in self.ocr_jobs.items()},
            "combined_pdfs": {k: v.model_dump() for k, v in self.combined_pdfs.items()},
            "protected_pdfs": {k: v.model_dump() for k, v in self.protected_pdfs.items()},
            "current_time": self.current_time,
            "pdf_counter": self.pdf_counter,
            "base_url": self.base_url
        }

    def _get_pdf_id_from_url(self, url: str) -> Optional[str]:
        """Extract PDF ID from URL or find by URL."""
        for pdf_id, pdf in self.pdfs.items():
            if pdf.url == url:
                return pdf_id
        return None

    def _generate_id(self) -> str:
        """Generate unique ID for resources."""
        self.pdf_counter += 1
        timestamp = self.current_time.replace("-", "").replace(":", "").replace("T", "")
        return f"pdf_{self.pdf_counter}_{timestamp}"

    def _generate_url(self, resource_type: str, resource_id: str) -> str:
        """Generate presigned URL for resource."""
        return f"{self.base_url}/{resource_type}/{resource_id}?token=sig{hash(resource_id) % 10000}"

    def create_pdf_from_html(self, html_content: str, output_filename: Optional[str], page_size: Optional[str]) -> dict:
        """
        Generate a PDF document from HTML content.
        """
        pdf_id = self._generate_id()
        page_count = max(1, len(html_content) // 3000)
        file_size = len(html_content) * 10
        
        url = self._generate_url("documents", pdf_id)
        if output_filename:
            url += f"&filename={output_filename}"
            
        pdf_doc = PDFDocument(
            id=pdf_id,
            url=url,
            page_count=page_count,
            file_size=file_size,
            source_type="html",
            created_at=self.current_time
        )
        self.pdfs[pdf_id] = pdf_doc
        
        return {
            "pdf_url": url,
            "page_count": page_count,
            "file_size": file_size
        }

    def export_pdf_to_format(self, pdf_url: str, target_format: str, output_filename: Optional[str]) -> dict:
        """
        Export a PDF document to alternative formats.
        """
        pdf_id = self._get_pdf_id_from_url(pdf_url)
        if not pdf_id or pdf_id not in self.pdfs:
            raise ValueError(f"PDF not found for URL: {pdf_url}")
            
        source_pdf = self.pdfs[pdf_id]
        export_id = self._generate_id()
        url = self._generate_url("exports", export_id)
        if output_filename:
            url += f"&filename={output_filename}"
            
        export_job = ExportJob(
            id=export_id,
            source_pdf_id=pdf_id,
            target_format=target_format,
            export_url=url,
            page_count=source_pdf.page_count,
            created_at=self.current_time
        )
        self.exports[export_id] = export_job
        
        return {
            "export_url": url,
            "format": target_format,
            "page_count": source_pdf.page_count
        }

    def ocr_pdf(self, pdf_url: str, language: Optional[str], output_type: Optional[str]) -> dict:
        """
        Perform optical character recognition on a PDF.
        """
        pdf_id = self._get_pdf_id_from_url(pdf_url)
        if not pdf_id or pdf_id not in self.pdfs:
            raise ValueError(f"PDF not found for URL: {pdf_url}")
            
        source_pdf = self.pdfs[pdf_id]
        ocr_id = self._generate_id()
        
        lang = language if language else "en-US"
        out_type = output_type if output_type else "searchable_pdf"
        
        url = self._generate_url("ocr", ocr_id)
        confidence = 95.0 if lang == "en-US" else 85.0
        
        extracted_text = None
        if out_type == "text_extraction":
            extracted_text = f"Extracted text from {source_pdf.page_count} pages. " * 20
            
        ocr_job = OCRJob(
            id=ocr_id,
            source_pdf_id=pdf_id,
            output_type=out_type,
            output_url=url,
            extracted_text=extracted_text,
            confidence_score=confidence,
            created_at=self.current_time
        )
        self.ocr_jobs[ocr_id] = ocr_job
        
        result = {
            "output_url": url,
            "confidence_score": confidence
        }
        if extracted_text is not None:
            result["extracted_text"] = extracted_text
            
        return result

    def combine_pdfs(self, pdf_urls: List[str], output_filename: Optional[str]) -> dict:
        """
        Merge multiple PDF documents into a single consolidated PDF file.
        """
        source_ids = []
        total_pages = 0
        
        for url in pdf_urls:
            pdf_id = self._get_pdf_id_from_url(url)
            if not pdf_id or pdf_id not in self.pdfs:
                raise ValueError(f"PDF not found for URL: {url}")
            source_ids.append(pdf_id)
            total_pages += self.pdfs[pdf_id].page_count
            
        combined_id = self._generate_id()
        url = self._generate_url("combined", combined_id)
        if output_filename:
            url += f"&filename={output_filename}"
            
        combined = CombinedPDF(
            id=combined_id,
            url=url,
            source_pdf_ids=source_ids,
            total_pages=total_pages,
            source_count=len(source_ids),
            created_at=self.current_time
        )
        self.combined_pdfs[combined_id] = combined
        
        return {
            "combined_pdf_url": url,
            "total_pages": total_pages,
            "source_count": len(source_ids)
        }

    def protect_pdf(self, pdf_url: str, password: str, permissions: Optional[dict]) -> dict:
        """
        Apply password protection and permission restrictions to a PDF document.
        """
        pdf_id = self._get_pdf_id_from_url(pdf_url)
        if not pdf_id or pdf_id not in self.pdfs:
            raise ValueError(f"PDF not found for URL: {pdf_url}")
            
        perms = {
            "printing": False,
            "copying": False,
            "editing": False,
            "commenting": False
        }
        
        if permissions:
            perms.update(permissions)
            
        protected_id = self._generate_id()
        url = self._generate_url("protected", protected_id)
        
        protected = ProtectedPDF(
            id=protected_id,
            source_pdf_id=pdf_id,
            url=url,
            encryption_level="AES-256",
            permissions=Permissions(**perms),
            created_at=self.current_time
        )
        self.protected_pdfs[protected_id] = protected
        
        return {
            "protected_pdf_url": url,
            "encryption_level": "AES-256",
            "permissions_applied": perms
        }

# Section 3: MCP Tools
mcp = FastMCP(name="AdobePDFServices")
api = AdobePDFAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the Adobe PDF Services API.

    Args:
        scenario (dict): Scenario dictionary matching AdobePDFScenario schema.

    Returns:
        success_message (str): Success message.
    """
    try:
        if not isinstance(scenario, dict):
            raise ValueError("Scenario must be a dictionary")
        api.load_scenario(scenario)
        return "Successfully loaded scenario"
    except Exception as e:
        raise e

@mcp.tool()
def save_scenario() -> dict:
    """
    Save current Adobe PDF Services state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def create_pdf_from_html(html_content: str, output_filename: Optional[str] = None, page_size: Optional[str] = None) -> dict:
    """
    Generate a PDF document from HTML content with configurable page dimensions.

    Args:
        html_content (str): The HTML content string to be rendered and converted into a PDF document.
        output_filename (str): [Optional] Custom filename for the generated output document. If omitted, a system-generated name is assigned.
        page_size (str): [Optional] The page size specification for the output PDF. Supported values: A4, Letter, Legal.

    Returns:
        pdf_url (str): The presigned URL for downloading the generated PDF document.
        page_count (int): The total number of pages in the generated PDF document.
        file_size (int): The size of the generated PDF file in bytes.
    """
    try:
        if not html_content or not isinstance(html_content, str):
            raise ValueError("html_content must be a non-empty string")
        if page_size and page_size not in ["A4", "Letter", "Legal"]:
            raise ValueError("page_size must be one of: A4, Letter, Legal")
        return api.create_pdf_from_html(html_content, output_filename, page_size)
    except Exception as e:
        raise e

@mcp.tool()
def export_pdf_to_format(pdf_url: str, target_format: str, output_filename: Optional[str] = None) -> dict:
    """
    Export a PDF document to alternative formats including Microsoft Office formats (Word, Excel, PowerPoint) or image files (JPEG, PNG).

    Args:
        pdf_url (str): The URL of the source PDF document to be converted to another format.
        target_format (str): The target export format. Supported formats: docx (Word), xlsx (Excel), pptx (PowerPoint), jpeg, png.
        output_filename (str): [Optional] Custom filename for the generated output document. If omitted, a system-generated name is assigned.

    Returns:
        export_url (str): The presigned URL for downloading the exported file in the target format.
        format (str): The format of the exported file, matching the requested target_format.
        page_count (int): The total number of pages in the exported document.
    """
    try:
        if not pdf_url or not isinstance(pdf_url, str):
            raise ValueError("pdf_url must be a non-empty string")
        if not target_format or not isinstance(target_format, str):
            raise ValueError("target_format must be a non-empty string")
        if target_format not in ["docx", "xlsx", "pptx", "jpeg", "png"]:
            raise ValueError("target_format must be one of: docx, xlsx, pptx, jpeg, png")
        return api.export_pdf_to_format(pdf_url, target_format, output_filename)
    except Exception as e:
        raise e

@mcp.tool()
def ocr_pdf(pdf_url: str, language: Optional[str] = None, output_type: Optional[str] = None) -> dict:
    """
    Perform optical character recognition on a PDF to extract text or create a searchable PDF document.

    Args:
        pdf_url (str): The URL of the source PDF document to be processed with OCR.
        language (str): [Optional] The language code of the document content for optimized OCR accuracy. Defaults to en-US (English, United States).
        output_type (str): [Optional] The desired OCR output type. 'searchable_pdf' creates a PDF with embedded text layer; 'text_extraction' extracts raw text content.

    Returns:
        output_url (str): The presigned URL for downloading the processed file (searchable PDF or text file depending on output_type).
        extracted_text (str): The raw extracted text content from the PDF. Only present when output_type is set to 'text_extraction'.
        confidence_score (float): The OCR accuracy confidence score ranging from 0 to 100, indicating the reliability of text recognition.
    """
    try:
        if not pdf_url or not isinstance(pdf_url, str):
            raise ValueError("pdf_url must be a non-empty string")
        if output_type and output_type not in ["searchable_pdf", "text_extraction"]:
            raise ValueError("output_type must be one of: searchable_pdf, text_extraction")
        return api.ocr_pdf(pdf_url, language, output_type)
    except Exception as e:
        raise e

@mcp.tool()
def combine_pdfs(pdf_urls: List[str], output_filename: Optional[str] = None) -> dict:
    """
    Merge multiple PDF documents into a single consolidated PDF file.

    Args:
        pdf_urls (List[str]): An ordered list of URLs pointing to the PDF documents to be merged. Documents are combined in the order provided.
        output_filename (str): [Optional] Custom filename for the generated output document. If omitted, a system-generated name is assigned.

    Returns:
        combined_pdf_url (str): The presigned URL for downloading the merged PDF document.
        total_pages (int): The total number of pages across all combined source documents.
        source_count (int): The number of source PDF documents that were merged.
    """
    try:
        if not pdf_urls or not isinstance(pdf_urls, list):
            raise ValueError("pdf_urls must be a non-empty list")
        if not all(isinstance(url, str) for url in pdf_urls):
            raise ValueError("All items in pdf_urls must be strings")
        return api.combine_pdfs(pdf_urls, output_filename)
    except Exception as e:
        raise e

@mcp.tool()
def protect_pdf(pdf_url: str, password: str, permissions: Optional[dict] = None) -> dict:
    """
    Apply password protection and configurable permission restrictions to secure a PDF document.

    Args:
        pdf_url (str): The URL of the source PDF document to be password protected.
        password (str): The password string used to encrypt and restrict access to the PDF document.
        permissions (dict): [Optional] Permission settings defining user restrictions for the protected PDF. If omitted, default restrictive permissions apply.
            Properties:
                printing (bool): Allow or deny printing of the PDF document.
                copying (bool): Allow or deny copying text and content from the PDF document.
                editing (bool): Allow or deny editing and modification of the PDF content.
                commenting (bool): Allow or deny adding annotations and comments to the PDF document.

    Returns:
        protected_pdf_url (str): The presigned URL for downloading the password-protected PDF document.
        encryption_level (str): The encryption standard applied to the PDF (e.g., AES-256).
        permissions_applied (dict): The complete set of permission restrictions that have been applied to the protected document.
            Properties:
                printing (bool): Indicates whether printing is permitted on the protected document.
                copying (bool): Indicates whether copying content is permitted on the protected document.
                editing (bool): Indicates whether editing content is permitted on the protected document.
                commenting (bool): Indicates whether adding comments is permitted on the protected document.
    """
    try:
        if not pdf_url or not isinstance(pdf_url, str):
            raise ValueError("pdf_url must be a non-empty string")
        if not password or not isinstance(password, str):
            raise ValueError("password must be a non-empty string")
        if permissions is not None and not isinstance(permissions, dict):
            raise ValueError("permissions must be a dictionary if provided")
        return api.protect_pdf(pdf_url, password, permissions)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()

