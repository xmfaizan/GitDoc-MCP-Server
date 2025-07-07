from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime

class RepoAnalysisRequest(BaseModel):
    repo_url: str
    branch: str = "main"
    include_patterns: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = [
        "node_modules", ".git", "__pycache__", ".pytest_cache",
        "venv", "env", ".env", "dist", "build", ".next"
    ]

class FileInfo(BaseModel):
    path: str
    name: str
    size: int
    language: str
    content: Optional[str] = None
    sha: str

class CodeAnalysis(BaseModel):
    file_path: str
    language: str
    summary: str
    complexity_score: float
    key_functions: List[str]
    dependencies: List[str]
    documentation_quality: float
    suggestions: List[str]

class DocumentationSection(BaseModel):
    title: str
    content: str
    code_examples: List[str] = []
    related_files: List[str] = []

class GeneratedDocumentation(BaseModel):
    repo_name: str
    repo_url: str
    overview: str
    installation_guide: str
    usage_examples: List[str]
    api_documentation: List[DocumentationSection]
    architecture_overview: str
    quality_score: float
    generated_at: datetime

class RepoAnalysisResponse(BaseModel):
    repo_info: Dict[str, Any]
    files: List[FileInfo]
    analysis: List[CodeAnalysis]
    documentation: GeneratedDocumentation
    processing_time: float

class CodeExplanationRequest(BaseModel):
    file_path: str
    code_snippet: str
    language: str
    context: Optional[str] = None

class CodeExplanationResponse(BaseModel):
    explanation: str
    key_concepts: List[str]
    best_practices: List[str]
    potential_issues: List[str]

class QualityMetrics(BaseModel):
    documentation_coverage: float
    code_complexity: float
    maintainability_score: float
    test_coverage: float
    overall_score: float
    recommendations: List[str]

class SearchRequest(BaseModel):
    query: str
    repo_name: str
    limit: int = 10

class SearchResult(BaseModel):
    file_path: str
    content: str
    relevance_score: float
    context: str