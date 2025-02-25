"""
Type definitions for post-processing functionality.
"""
from typing import List, Dict, Any, Optional, Literal


class FormatConversionOptions:
    """Options for format conversion."""
    source_format: str
    target_format: str
    include_metadata: bool
    include_images: bool
    
    def __init__(
        self,
        source_format: str,
        target_format: str,
        include_metadata: bool = True,
        include_images: bool = True
    ):
        self.source_format = source_format
        self.target_format = target_format
        self.include_metadata = include_metadata
        self.include_images = include_images


class ProofreadingOptions:
    """Options for proofreading."""
    check_grammar: bool
    check_spelling: bool
    check_style: bool
    check_plagiarism: bool
    
    def __init__(
        self,
        check_grammar: bool = True,
        check_spelling: bool = True,
        check_style: bool = True,
        check_plagiarism: bool = False
    ):
        self.check_grammar = check_grammar
        self.check_spelling = check_spelling
        self.check_style = check_style
        self.check_plagiarism = check_plagiarism


class ProofreadingIssue:
    """An issue found during proofreading."""
    type: str
    text: str
    position: Dict[str, int]
    suggestion: Optional[str]
    
    def __init__(
        self,
        type: str,
        text: str,
        position: Dict[str, int],
        suggestion: Optional[str] = None
    ):
        self.type = type
        self.text = text
        self.position = position
        self.suggestion = suggestion


class ProofreadingResult:
    """Results from proofreading."""
    issues: List[ProofreadingIssue]
    corrected_text: Optional[str]
    
    def __init__(self, issues: List[ProofreadingIssue], corrected_text: Optional[str] = None):
        self.issues = issues
        self.corrected_text = corrected_text


class HumanizationOptions:
    """Options for humanizing content."""
    tone: str
    formality: str
    personality: str
    
    def __init__(
        self,
        tone: str = "casual",
        formality: str = "neutral",
        personality: str = "friendly"
    ):
        self.tone = tone
        self.formality = formality
        self.personality = personality


class SaveOptions:
    """Options for saving content to a file."""
    file_path: str
    format: str
    overwrite: bool
    
    def __init__(self, file_path: str, format: str = "markdown", overwrite: bool = False):
        self.file_path = file_path
        self.format = format
        self.overwrite = overwrite


OutputFormat = Literal["markdown", "html", "docx", "pdf", "txt"]


class PostProcessingOptions:
    """Options for post-processing."""
    format_conversion: Optional[FormatConversionOptions]
    proofreading: Optional[ProofreadingOptions]
    humanization: Optional[HumanizationOptions]
    save: Optional[SaveOptions]
    
    def __init__(
        self,
        format_conversion: Optional[FormatConversionOptions] = None,
        proofreading: Optional[ProofreadingOptions] = None,
        humanization: Optional[HumanizationOptions] = None,
        save: Optional[SaveOptions] = None
    ):
        self.format_conversion = format_conversion
        self.proofreading = proofreading
        self.humanization = humanization
        self.save = save
