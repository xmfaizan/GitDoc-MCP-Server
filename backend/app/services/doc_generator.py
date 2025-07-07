import asyncio
import json
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..config import settings
from ..models import (
    GeneratedDocumentation, DocumentationSection, 
    CodeAnalysis, FileInfo, QualityMetrics
)

class DocumentationGenerator:
    def __init__(self):
        self.openai_api_key = settings.OPENAI_API_KEY
        self.api_url = "https://api.openai.com/v1/chat/completions"

    async def generate_documentation(self, repo_info: Dict[str, Any], 
                                   files: List[FileInfo], 
                                   analysis_results: List[CodeAnalysis]) -> GeneratedDocumentation:
        try:
            overview = await self._generate_overview(repo_info, files, analysis_results)
            installation_guide = self._generate_installation_guide(repo_info, files)
            usage_examples = await self._generate_usage_examples(repo_info, files, analysis_results)
            api_docs = await self._generate_api_documentation(analysis_results)
            architecture = await self._generate_architecture_overview(repo_info, files, analysis_results)
            quality_score = self._calculate_quality_score(analysis_results)
            
            return GeneratedDocumentation(
                repo_name=repo_info.get("name", "Unknown Repository"),
                repo_url=repo_info.get("clone_url", ""),
                overview=overview,
                installation_guide=installation_guide,
                usage_examples=usage_examples,
                api_documentation=api_docs,
                architecture_overview=architecture,
                quality_score=quality_score,
                generated_at=datetime.now()
            )
            
        except Exception as e:
            print(f"Error generating documentation: {str(e)}")
            return self._generate_fallback_documentation(repo_info, files, analysis_results)

    async def _generate_overview(self, repo_info: Dict, files: List[FileInfo], 
                                analysis_results: List[CodeAnalysis]) -> str:
        try:
            languages = list(set([f.language for f in files if f.language != "text"]))
            main_language = max(set([a.language for a in analysis_results]), 
                              key=[a.language for a in analysis_results].count) if analysis_results else "Unknown"
            
            file_count = len(files)
            function_count = sum(len(a.key_functions) for a in analysis_results)
            
            basic_overview = f"""# {repo_info.get('name', 'Repository')}

{repo_info.get('description', 'A software project with comprehensive documentation.')}

## Quick Overview
- **Primary Language**: {main_language}
- **Languages Used**: {', '.join(languages[:5])}
- **Total Files**: {file_count}
- **Functions/Classes**: {function_count}
- **Last Updated**: {repo_info.get('updated_at', 'Unknown')}"""

            if self.openai_api_key and analysis_results:
                ai_overview = await self._generate_ai_overview(repo_info, analysis_results)
                if ai_overview:
                    return f"{basic_overview}\n\n{ai_overview}"
            
            return basic_overview
            
        except Exception as e:
            print(f"Error generating overview: {str(e)}")
            return f"# {repo_info.get('name', 'Repository')}\n\n{repo_info.get('description', 'A software project.')}"

    async def _generate_ai_overview(self, repo_info: Dict, analysis_results: List[CodeAnalysis]) -> Optional[str]:
        try:
            code_summaries = [f"- {a.file_path}: {a.summary}" for a in analysis_results[:10]]
            
            prompt = f"""Based on this code analysis, write a comprehensive project overview:

Repository: {repo_info.get('name')}
Description: {repo_info.get('description', '')}

Code Analysis:
{chr(10).join(code_summaries)}

Write a detailed overview that includes:
1. What this project does
2. Key features and capabilities  
3. Target audience or use cases
4. Notable technical aspects

Keep it informative and engaging, suitable for a README file."""

            response = await self._call_openai_api(prompt)
            return response
            
        except Exception as e:
            print(f"AI overview generation failed: {str(e)}")
            return None

    def _generate_installation_guide(self, repo_info: Dict, files: List[FileInfo]) -> str:
        file_names = [f.name.lower() for f in files]
        languages = set([f.language for f in files if f.language != "text"])
        
        installation_steps = ["## Installation\n"]
        
        # Clone repository
        clone_url = repo_info.get('clone_url', '')
        if clone_url:
            installation_steps.append(f"1. **Clone the repository**\n```bash\ngit clone {clone_url}\ncd {repo_info.get('name', 'repository')}\n```\n")
        
        # Language-specific installations
        if "python" in languages:
            if any("requirements.txt" in name for name in file_names):
                installation_steps.append("2. **Install Python dependencies**\n```bash\npip install -r requirements.txt\n```\n")
            elif any("pyproject.toml" in name for name in file_names):
                installation_steps.append("2. **Install Python dependencies**\n```bash\npip install .\n```\n")
            else:
                installation_steps.append("2. **Install Python dependencies**\n```bash\npip install -r requirements.txt\n```\n")
        
        if "javascript" in languages or "typescript" in languages:
            if any("package.json" in name for name in file_names):
                installation_steps.append("3. **Install Node.js dependencies**\n```bash\nnpm install\n```\n")
        
        if "java" in languages:
            if any("pom.xml" in name for name in file_names):
                installation_steps.append("3. **Build with Maven**\n```bash\nmvn clean install\n```\n")
            elif any("build.gradle" in name for name in file_names):
                installation_steps.append("3. **Build with Gradle**\n```bash\n./gradlew build\n```\n")
        
        if "go" in languages:
            installation_steps.append("3. **Build Go application**\n```bash\ngo mod download\ngo build\n```\n")
        
        if "rust" in languages:
            installation_steps.append("3. **Build Rust application**\n```bash\ncargo build --release\n```\n")
        
        # Environment setup
        if any(".env" in name for name in file_names):
            installation_steps.append("4. **Environment Setup**\n```bash\ncp .env.example .env\n# Edit .env with your configuration\n```\n")
        
        return "".join(installation_steps)

    async def _generate_usage_examples(self, repo_info: Dict, files: List[FileInfo], 
                                     analysis_results: List[CodeAnalysis]) -> List[str]:
        examples = []
        
        # Basic usage based on main files
        main_files = [f for f in files if f.name.lower() in ['main.py', 'index.js', 'app.py', 'server.js', 'main.go']]
        
        if main_files:
            main_file = main_files[0]
            if main_file.language == "python":
                examples.append("```python\n# Basic usage\npython main.py\n```")
            elif main_file.language == "javascript":
                examples.append("```bash\n# Start the application\nnode index.js\n# or\nnpm start\n```")
            elif main_file.language == "go":
                examples.append("```bash\n# Run the application\ngo run main.go\n```")
        
        # API usage examples based on analysis
        api_functions = []
        for analysis in analysis_results:
            api_functions.extend([f for f in analysis.key_functions if any(keyword in f.lower() 
                                for keyword in ['api', 'endpoint', 'route', 'handler'])])
        
        if api_functions:
            examples.append(f"```python\n# API Usage Example\n# Available endpoints: {', '.join(api_functions[:3])}\n```")
        
        # Generate AI examples if available
        if self.openai_api_key and analysis_results:
            ai_examples = await self._generate_ai_usage_examples(repo_info, analysis_results)
            if ai_examples:
                examples.extend(ai_examples)
        
        return examples if examples else ["```bash\n# Usage examples will be added soon\n```"]

    async def _generate_ai_usage_examples(self, repo_info: Dict, analysis_results: List[CodeAnalysis]) -> List[str]:
        try:
            functions_summary = []
            for analysis in analysis_results[:5]:
                if analysis.key_functions:
                    functions_summary.append(f"{analysis.file_path}: {', '.join(analysis.key_functions[:3])}")
            
            prompt = f"""Generate practical usage examples for this {repo_info.get('name')} project:

Key Functions Found:
{chr(10).join(functions_summary)}

Generate 2-3 realistic usage examples showing:
1. Basic usage/getting started
2. Common use case example
3. Advanced usage (if applicable)

Format as markdown code blocks with appropriate language syntax highlighting."""

            response = await self._call_openai_api(prompt)
            
            if response:
                # Split response into individual code blocks
                examples = []
                blocks = response.split("```")
                for i in range(1, len(blocks), 2):  # Every other block is code
                    if i < len(blocks):
                        examples.append(f"```{blocks[i]}```")
                return examples[:3]
            
            return []
            
        except Exception as e:
            print(f"AI usage examples generation failed: {str(e)}")
            return []

    async def _generate_api_documentation(self, analysis_results: List[CodeAnalysis]) -> List[DocumentationSection]:
        api_sections = []
        
        for analysis in analysis_results:
            if analysis.key_functions:
                # Group functions by file
                section = DocumentationSection(
                    title=f"API - {analysis.file_path}",
                    content=f"**Language**: {analysis.language}\n\n**Summary**: {analysis.summary}\n\n**Functions/Classes**:\n" + 
                           "\n".join([f"- `{func}`" for func in analysis.key_functions]),
                    code_examples=[],
                    related_files=[analysis.file_path]
                )
                
                # Add dependencies if available
                if analysis.dependencies:
                    section.content += f"\n\n**Dependencies**: {', '.join(analysis.dependencies)}"
                
                api_sections.append(section)
        
        # Generate AI-enhanced API docs if available
        if self.openai_api_key and analysis_results:
            enhanced_sections = await self._enhance_api_documentation(api_sections)
            return enhanced_sections
        
        return api_sections[:10]  # Limit to prevent overwhelming

    async def _enhance_api_documentation(self, sections: List[DocumentationSection]) -> List[DocumentationSection]:
        enhanced_sections = []
        
        for section in sections[:5]:  # Limit API calls
            try:
                prompt = f"""Enhance this API documentation section:

Title: {section.title}
Content: {section.content}

Make it more comprehensive by adding:
1. Brief description of each function's purpose
2. Expected parameters (if determinable)
3. Return values or behavior
4. Usage notes

Keep the same title but improve the content to be more helpful for developers."""

                enhanced_content = await self._call_openai_api(prompt)
                
                if enhanced_content:
                    section.content = enhanced_content
                
                enhanced_sections.append(section)
                
            except Exception as e:
                print(f"Error enhancing API docs: {str(e)}")
                enhanced_sections.append(section)
        
        return enhanced_sections

    async def _generate_architecture_overview(self, repo_info: Dict, files: List[FileInfo], 
                                            analysis_results: List[CodeAnalysis]) -> str:
        try:
            # Basic architecture analysis
            file_structure = {}
            for file in files:
                parts = file.path.split('/')
                if len(parts) > 1:
                    folder = parts[0]
                    file_structure[folder] = file_structure.get(folder, 0) + 1
            
            languages = list(set([f.language for f in files if f.language != "text"]))
            complexity_avg = sum(a.complexity_score for a in analysis_results) / len(analysis_results) if analysis_results else 0
            
            basic_arch = f"""## Architecture Overview

### Project Structure
{chr(10).join([f"- **{folder}**: {count} files" for folder, count in file_structure.items()])}

### Technology Stack
- **Languages**: {', '.join(languages)}
- **Average Complexity**: {complexity_avg:.1f}/10
- **Total Components**: {len(analysis_results)}

### Code Organization
- Well-structured project with {len(file_structure)} main directories
- Complexity level: {"High" if complexity_avg > 7 else "Medium" if complexity_avg > 4 else "Low"}
"""

            if self.openai_api_key:
                ai_arch = await self._generate_ai_architecture(repo_info, files, analysis_results)
                if ai_arch:
                    return f"{basic_arch}\n\n{ai_arch}"
            
            return basic_arch
            
        except Exception as e:
            print(f"Error generating architecture overview: {str(e)}")
            return "## Architecture Overview\n\nArchitecture analysis is being generated..."

    async def _generate_ai_architecture(self, repo_info: Dict, files: List[FileInfo], 
                                      analysis_results: List[CodeAnalysis]) -> Optional[str]:
        try:
            file_summary = [f"{f.path} ({f.language})" for f in files[:15]]
            
            prompt = f"""Analyze the architecture of this software project:

Project: {repo_info.get('name')}
Files: {chr(10).join(file_summary)}

Provide architectural insights including:
1. Overall design pattern or architecture style
2. Key architectural components
3. Data flow and interactions
4. Scalability considerations
5. Architectural strengths and potential improvements

Focus on high-level architecture rather than code details."""

            response = await self._call_openai_api(prompt)
            return response
            
        except Exception as e:
            print(f"AI architecture generation failed: {str(e)}")
            return None

    def calculate_quality_metrics(self, analysis_results: List[CodeAnalysis]) -> QualityMetrics:
        if not analysis_results:
            return QualityMetrics(
                documentation_coverage=0.0,
                code_complexity=0.0,
                maintainability_score=0.0,
                test_coverage=0.0,
                overall_score=0.0,
                recommendations=["No code analysis available"]
            )
        
        doc_scores = [a.documentation_quality for a in analysis_results]
        complexity_scores = [a.complexity_score for a in analysis_results]
        
        doc_coverage = sum(doc_scores) / len(doc_scores)
        avg_complexity = sum(complexity_scores) / len(complexity_scores)
        
        # Maintainability score (inverse of complexity + documentation)
        maintainability = (doc_coverage + (10 - avg_complexity)) / 2
        
        # Test coverage estimation (basic heuristic)
        test_files = sum(1 for a in analysis_results if 'test' in a.file_path.lower())
        test_coverage = min((test_files / len(analysis_results)) * 100, 100) if analysis_results else 0
        
        overall = (doc_coverage * 0.3 + (10 - avg_complexity) * 0.3 + 
                  maintainability * 0.2 + (test_coverage / 10) * 0.2)
        
        recommendations = []
        if doc_coverage < 5:
            recommendations.append("Improve code documentation and comments")
        if avg_complexity > 7:
            recommendations.append("Reduce code complexity by refactoring large functions")
        if test_coverage < 30:
            recommendations.append("Add more unit tests for better coverage")
        if not recommendations:
            recommendations.append("Code quality is good, maintain current standards")
        
        return QualityMetrics(
            documentation_coverage=round(doc_coverage, 1),
            code_complexity=round(avg_complexity, 1),
            maintainability_score=round(maintainability, 1),
            test_coverage=round(test_coverage, 1),
            overall_score=round(overall, 1),
            recommendations=recommendations
        )

    def _calculate_quality_score(self, analysis_results: List[CodeAnalysis]) -> float:
        if not analysis_results:
            return 0.0
        
        doc_scores = [a.documentation_quality for a in analysis_results]
        complexity_scores = [a.complexity_score for a in analysis_results]
        
        avg_doc = sum(doc_scores) / len(doc_scores)
        avg_complexity = sum(complexity_scores) / len(complexity_scores)
        
        # Quality score: good documentation + low complexity = high quality
        quality_score = (avg_doc + (10 - avg_complexity)) / 2
        
        return round(min(quality_score, 10.0), 1)

    async def _call_openai_api(self, prompt: str) -> Optional[str]:
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "You are a technical documentation expert. Create clear, comprehensive documentation."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 2000,
                "temperature": 0.2
            }
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                print(f"OpenAI API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"OpenAI API call failed: {str(e)}")
            return None

    def _generate_fallback_documentation(self, repo_info: Dict, files: List[FileInfo], 
                                       analysis_results: List[CodeAnalysis]) -> GeneratedDocumentation:
        return GeneratedDocumentation(
            repo_name=repo_info.get("name", "Repository"),
            repo_url=repo_info.get("clone_url", ""),
            overview=f"# {repo_info.get('name', 'Repository')}\n\n{repo_info.get('description', 'A software project.')}",
            installation_guide="## Installation\n\nInstallation instructions will be generated based on project structure.",
            usage_examples=["```bash\n# Usage examples coming soon\n```"],
            api_documentation=[],
            architecture_overview="## Architecture\n\nArchitecture overview is being generated...",
            quality_score=5.0,
            generated_at=datetime.now()
        )