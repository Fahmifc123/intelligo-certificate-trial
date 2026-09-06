"""
Certificate generation service module.
Uses python-pptx to edit PPTX template and converts to PDF.
"""
import os
import uuid
import subprocess
from datetime import datetime
from config import CERTIFICATES_DIRECTORY, logger

# Check for required libraries
try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    PYPPTX_AVAILABLE = True
except ImportError:
    PYPPTX_AVAILABLE = False
    logger.warning("python-pptx not installed. Run: pip install python-pptx")

# Path to LibreOffice for conversion (fallback if comtypes not available)
LIBREOFFICE_PATH = "soffice"  # Usually in PATH on Linux, or specific path on Windows


def _replace_text_in_shape(shape, replacements, font_size_overrides=None):
    """
    Replace multiple placeholders in a shape while preserving font formatting.
    replacements: dict of {old_text: new_text}
    font_size_overrides: optional dict of {old_text: Pt(...)} to force a
        specific font size for the run instead of preserving the template's.
    """
    if not hasattr(shape, "text_frame"):
        return False

    # Get all text from shape
    full_text = shape.text
    if not any(placeholder in full_text for placeholder in replacements.keys()):
        return False

    font_size_overrides = font_size_overrides or {}

    # Process each paragraph
    for para in shape.text_frame.paragraphs:
        for run in para.runs:
            for old_text, new_text in replacements.items():
                if old_text in run.text:
                    # Get font properties before replacement
                    font_name = run.font.name
                    font_size = font_size_overrides.get(old_text, run.font.size)
                    font_bold = run.font.bold
                    font_italic = run.font.italic
                    font_color = None
                    try:
                        if run.font.color and run.font.color.rgb:
                            font_color = run.font.color.rgb
                    except:
                        pass

                    # Replace the text
                    run.text = run.text.replace(old_text, new_text)

                    # Re-apply font properties (they might reset)
                    try:
                        if font_name:
                            run.font.name = font_name
                        if font_size:
                            run.font.size = font_size
                        if font_bold is not None:
                            run.font.bold = font_bold
                        if font_italic is not None:
                            run.font.italic = font_italic
                        if font_color:
                            run.font.color.rgb = font_color
                    except:
                        pass
                    break  # Move to next run after successful replacement
    return True


def _get_output_directory():
    """Get the output directory for generated certificates."""
    # Use backend directory as base (parent of services/)
    backend_dir = os.path.dirname(os.path.dirname(__file__))
    output_dir = os.path.join(backend_dir, "static", "certificates", "generate")
    abs_output_dir = os.path.abspath(output_dir)
    return abs_output_dir


def _get_title_prefix(project_title: str) -> str:
    """
    Generate certificate ID prefix based on project title.
    - "Trial Bootcamp Data Science & AI" → TBDSAI
    - "Trial Bootcamp Data Science" → TBDS
    - "Trial Bootcamp Artificial Intelligence" or "Trial Bootcamp AI" → TBAI
    """
    title_upper = project_title.upper()
    
    if "DATA SCIENCE & AI" in title_upper or "DATA SCIENCE AND AI" in title_upper:
        return "TBDSAI"
    elif "DATA SCIENCE" in title_upper:
        return "TBDS"
    elif "ARTIFICIAL INTELLIGENCE" in title_upper or ("TRIAL BOOTCAMP AI" in title_upper and "DATA SCIENCE" not in title_upper):
        return "TBAI"
    else:
        return "TBDSAI"  # Default


def _remove_paragraphs_containing(shape, placeholder: str) -> None:
    """
    Delete any paragraph in the shape's text frame whose text contains
    `placeholder`, removing it entirely (no blank line left behind).
    """
    if not hasattr(shape, "text_frame"):
        return

    for para in list(shape.text_frame.paragraphs):
        if placeholder in para.text:
            para._p.getparent().remove(para._p)


def generate_certificate(name: str, program_title: str) -> str:
    """
    Generate a PDF certificate by editing the PPTX template and converting to PDF.

    Args:
        name: Participant name
        program_title: Program name (e.g., "Trial Bootcamp Data Science & AI - Intelligo ID")

    Dynamic placeholders replaced:
    - {{NAMA}} - Participant name
    - {{JUDUL}} - Program title
    - {{id}} - Certificate ID

    The "held from {{PELAKSANAAN}}" line is removed entirely since trial
    execution dates are no longer tracked per-submission.
    """
    if not PYPPTX_AVAILABLE:
        raise RuntimeError("python-pptx is required. Install with: pip install python-pptx")

    # Generate unique filename and issue ID
    file_id = str(uuid.uuid4())[:4].upper()
    
    # Generate prefix based on program_title (for ID)
    title_prefix = _get_title_prefix(program_title)
    
    # Use current date for ID (MMYY format)
    date_for_id = datetime.now().strftime("%m%y")
    
    issue_id = f"INT-{title_prefix}-{date_for_id}-{file_id}"
    filename = f"{file_id}.pdf"
    pptx_filename = f"{file_id}.pptx"
    
    # Get directories
    output_dir = _get_output_directory()
    os.makedirs(output_dir, exist_ok=True)
    
    pptx_filepath = os.path.join(output_dir, pptx_filename)
    pdf_filepath = os.path.join(output_dir, filename)
    
    # Get template path
    template_path = os.path.join(
        os.path.dirname(__file__), 
        "..", 
        "static", 
        "certificates", 
        "Template of Certificate Intelligo.pptx"
    )
    template_path = os.path.abspath(template_path)
    
    # Load the presentation
    prs = Presentation(template_path)
    slide = prs.slides[0]
    
    # Define all replacements (will preserve font from template)
    replacements = {
        "{{NAMA}}": name,
        "{{JUDUL}}": program_title,
        "{{id}}": issue_id
    }

    # The Certificate ID box is narrow; the full ID string ("Certificate ID :
    # INT-TBDSAI-0926-XXXX") wraps onto a second line at the template's
    # default 11pt and overflows into the footer graphic below it. Shrink
    # just that line so it reliably fits on one line.
    font_size_overrides = {"{{id}}": Pt(9)}

    # Replace placeholders in all shapes, and drop the execution-date line
    # entirely (no start/end date is collected anymore).
    for shape in slide.shapes:
        _remove_paragraphs_containing(shape, "{{PELAKSANAAN}}")
        _replace_text_in_shape(shape, replacements, font_size_overrides)

    # Save the modified PPTX
    prs.save(pptx_filepath)

    try:
        # Convert PPTX to PDF
        _convert_pptx_to_pdf(pptx_filepath, pdf_filepath)
    finally:
        # Always remove the temporary PPTX file, even if conversion failed,
        # so failed attempts don't leak files into the generate/ directory.
        if os.path.exists(pptx_filepath):
            os.remove(pptx_filepath)

    return filename


def _convert_pptx_to_pdf(pptx_path: str, pdf_path: str) -> bool:
    """
    Convert PPTX to PDF using LibreOffice (Linux/macOS) or PowerPoint COM (Windows).
    """
    import platform
    
    pptx_path = os.path.abspath(pptx_path)
    pdf_path = os.path.abspath(pdf_path)
    output_dir = os.path.dirname(pdf_path)
    pdf_filename = os.path.basename(pdf_path)
    
    is_windows = platform.system() == "Windows"
    
    if is_windows:
        # Method: Use PowerPoint COM (Windows only)
        try:
            import comtypes.client

            abs_pptx = os.path.abspath(pptx_path)
            abs_pdf = os.path.abspath(pdf_path)
            
            powerpoint = comtypes.client.CreateObject("PowerPoint.Application")
            presentation = powerpoint.Presentations.Open(abs_pptx, WithWindow=False)
            presentation.SaveAs(abs_pdf, 32)  # 32 = ppSaveAsPDF
            presentation.Close()
            powerpoint.Quit()
            
            return True
        except ImportError:
            logger.error("comtypes not installed. Run: pip install comtypes")
        except Exception as e:
            logger.error(f"PowerPoint COM conversion failed: {e}")
        
        raise RuntimeError(
            "Cannot convert PPTX to PDF. Please install comtypes: pip install comtypes"
        )
    else:
        # Method: Use LibreOffice (Linux/macOS)
        try:
            # Use impress_pdf_Export for PowerPoint files (not writer_pdf_Export)
            cmd = [
                "soffice",
                "--headless",
                "--norestore",
                "--nofirststartwizard",
                "--convert-to", "pdf:impress_pdf_Export",
                "--outdir", output_dir,
                pptx_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=output_dir
            )
            
            # Check if PDF was created with expected name
            if os.path.exists(pdf_path):
                logger.info("PDF generated successfully")
                return True
        
        except FileNotFoundError:
            logger.error("LibreOffice (soffice) not found in PATH")
        except Exception as e:
            logger.error(f"LibreOffice conversion error: {e}")
        
        raise RuntimeError(
            "Cannot convert PPTX to PDF. Install LibreOffice: https://www.libreoffice.org/download/"
        )
