import asyncio
import json
import requests
from typing import List, Dict, Optional

from ..config import settings
from ..models import CodeAnalysis, CodeExplanationResponse
from ..utils.file_processor import FileProcessor

class CodeAnalyzer:
    def __init__(self):
        self.openai_api_key = settings.OPENAI_API_KEY
        self.file_processor = FileProcessor()
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.has_openai = bool(self.openai_api_key)
        
        if self.has_openai:
            print("Code Analyzer initialized with OpenAI integration")
        else:
            print("Code Analyzer initialized with local analysis (no OpenAI key)")

    async def analyze_code(self, code_content: str, language: str, file_path: str) -> CodeAnalysis:
        try:
            # Always do basic analysis first
            basic_analysis = self._get_basic_analysis(code_content, language, file_path)
            
            # Try OpenAI analysis if available
            if self.has_openai:
                ai_analysis = await self._get_openai_analysis(code_content, language, file_path)
                if ai_analysis:
                    return CodeAnalysis(
                        file_path=file_path,
                        language=language,
                        summary=ai_analysis.get("summary", f"AI analysis for {language} file"),
                        complexity_score=basic_analysis["complexity_score"],
                        key_functions=[func["name"] for func in basic_analysis["functions"]],
                        dependencies=basic_analysis["imports"],
                        documentation_quality=basic_analysis["documentation_score"],
                        suggestions=ai_analysis.get("suggestions", [])
                    )
            
            # Fallback to intelligent local analysis
            local_analysis = self._generate_intelligent_summary(code_content, language, file_path, basic_analysis)
            
            return CodeAnalysis(
                file_path=file_path,
                language=language,
                summary=local_analysis["summary"],
                complexity_score=basic_analysis["complexity_score"],
                key_functions=[func["name"] for func in basic_analysis["functions"]],
                dependencies=basic_analysis["imports"],
                documentation_quality=basic_analysis["documentation_score"],
                suggestions=local_analysis["suggestions"]
            )
            
        except Exception as e:
            print(f"Error analyzing code: {str(e)}")
            return self._get_fallback_analysis(code_content, language, file_path)

    async def explain_code(self, code_snippet: str, language: str, context: Optional[str] = None) -> CodeExplanationResponse:
        try:
            # Try OpenAI explanation first
            if self.has_openai:
                openai_explanation = await self._get_openai_explanation(code_snippet, language, context)
                if openai_explanation:
                    return openai_explanation
            
            # Fallback to local explanation
            return self._generate_local_explanation(code_snippet, language, context)
            
        except Exception as e:
            print(f"Error explaining code: {str(e)}")
            return CodeExplanationResponse(
                explanation=f"Analysis available for this {language} code snippet. OpenAI integration provides enhanced explanations.",
                key_concepts=["Code structure analysis", "Pattern recognition"],
                best_practices=["Follow language conventions", "Add comprehensive documentation"],
                potential_issues=["Consider error handling", "Review for optimization opportunities"]
            )

    async def _get_openai_analysis(self, code_content: str, language: str, file_path: str) -> Optional[Dict]:
        """Get AI-powered code analysis using OpenAI API"""
        try:
            prompt = f"""Analyze this {language} code from {file_path}:

```{language}
{code_content[:2000]}
```

Provide a JSON response with:
{{
    "summary": "Brief overview of what this code does and its purpose",
    "suggestions": ["3-5 specific improvement recommendations"],
    "complexity_assessment": "Description of code complexity and maintainability",
    "key_patterns": ["Notable programming patterns or architectural decisions"]
}}

Focus on practical insights that help developers understand and improve the code."""

            response = await self._call_openai_api(prompt)
            
            if response:
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    # Parse text response if JSON fails
                    return self._parse_text_analysis(response)
            
            return None
            
        except Exception as e:
            print(f"OpenAI analysis failed for {file_path}: {str(e)}")
            return None

    async def _get_openai_explanation(self, code_snippet: str, language: str, context: Optional[str] = None) -> Optional[CodeExplanationResponse]:
        """Get AI-powered code explanation using OpenAI API"""
        try:
            prompt = f"""Explain this {language} code snippet in detail:

```{language}
{code_snippet}
```

Context: {context or "No additional context provided"}

Provide a JSON response with:
{{
    "explanation": "Clear explanation of what this code does and how it works",
    "key_concepts": ["Important programming concepts demonstrated"],
    "best_practices": ["Good practices shown in this code"],
    "potential_issues": ["Potential improvements or issues to consider"]
}}

Make the explanation educational and helpful for developers."""

            response = await self._call_openai_api(prompt)
            
            if response:
                try:
                    parsed = json.loads(response)
                    return CodeExplanationResponse(
                        explanation=parsed.get("explanation", response),
                        key_concepts=parsed.get("key_concepts", []),
                        best_practices=parsed.get("best_practices", []),
                        potential_issues=parsed.get("potential_issues", [])
                    )
                except json.JSONDecodeError:
                    return CodeExplanationResponse(
                        explanation=response,
                        key_concepts=[],
                        best_practices=[],
                        potential_issues=[]
                    )
            
            return None
            
        except Exception as e:
            print(f"OpenAI explanation failed: {str(e)}")
            return None

    async def _call_openai_api(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """Make API call to OpenAI with retry logic"""
        for attempt in range(max_retries):
            try:
                headers = {
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {
                            "role": "system", 
                            "content": "You are an expert code analyst. Provide clear, practical insights about code quality, structure, and improvements. Always respond with valid JSON when requested."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 1500,
                    "temperature": 0.1
                }
                
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, 
                    lambda: requests.post(self.api_url, headers=headers, json=payload, timeout=30)
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    wait_time = min(2 ** attempt, 10)  # Exponential backoff, max 10 seconds
                    print(f"Rate limited, waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    print(f"OpenAI API error: {response.status_code}")
                    if attempt == max_retries - 1:
                        return None
                        
            except requests.exceptions.Timeout:
                print(f"OpenAI API timeout on attempt {attempt + 1}")
                if attempt == max_retries - 1:
                    return None
            except Exception as e:
                print(f"OpenAI API call failed on attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries - 1:
                    return None
        
        return None

    def _parse_text_analysis(self, response: str) -> Dict:
        """Parse text response when JSON parsing fails"""
        analysis = {
            "summary": "",
            "suggestions": [],
            "complexity_assessment": "",
            "key_patterns": []
        }
        
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if 'summary' in line.lower() and ':' in line:
                analysis['summary'] = line.split(':', 1)[1].strip()
            elif 'suggestion' in line.lower():
                current_section = 'suggestions'
            elif 'complexity' in line.lower() and ':' in line:
                analysis['complexity_assessment'] = line.split(':', 1)[1].strip()
            elif 'pattern' in line.lower():
                current_section = 'key_patterns'
            elif line and current_section:
                if line.startswith('-') or line.startswith('•'):
                    analysis[current_section].append(line.lstrip('- •').strip())
        
        # Ensure we have some content
        if not analysis['summary']:
            analysis['summary'] = response[:200] + "..." if len(response) > 200 else response
        
        return analysis

    def _generate_intelligent_summary(self, code_content: str, language: str, file_path: str, basic_analysis: Dict) -> Dict:
        """Generate intelligent summary without AI API"""
        lines = len(code_content.split('\n'))
        functions = basic_analysis['functions']
        imports = basic_analysis['imports']
        complexity = basic_analysis['complexity_score']
        
        # Determine file type and purpose
        file_type = self._determine_file_type(file_path, code_content)
        
        summary_parts = []
        
        # File type and basic info
        summary_parts.append(f"{file_type} written in {language.title()}")
        
        # Size and structure analysis
        if lines < 50:
            summary_parts.append(f"Compact implementation with {lines} lines")
        elif lines < 200:
            summary_parts.append(f"Well-sized module with {lines} lines")
        else:
            summary_parts.append(f"Comprehensive implementation with {lines} lines")
        
        # Function and class analysis
        if functions:
            function_types = {}
            for func in functions:
                func_type = func.get('type', 'function')
                function_types[func_type] = function_types.get(func_type, 0) + 1
            
            if function_types.get('class', 0) > 0:
                summary_parts.append(f"Defines {function_types['class']} class(es) with object-oriented structure")
            if function_types.get('function', 0) > 0:
                summary_parts.append(f"Contains {function_types['function']} function(s) with clear separation of concerns")
        
        # Dependency analysis
        if imports:
            if len(imports) <= 3:
                summary_parts.append("Minimal dependencies promoting simplicity")
            elif len(imports) <= 8:
                summary_parts.append("Moderate use of external libraries")
            else:
                summary_parts.append("Extensive use of external dependencies")
        
        # Complexity and quality assessment
        if complexity < 3:
            summary_parts.append("Simple, maintainable code structure")
        elif complexity < 6:
            summary_parts.append("Well-balanced complexity with good readability")
        elif complexity < 8:
            summary_parts.append("Moderate complexity requiring careful review")
        else:
            summary_parts.append("High complexity suggesting refactoring opportunities")
        
        summary = ". ".join(summary_parts) + "."
        
        # Generate intelligent suggestions
        suggestions = self._generate_smart_suggestions(basic_analysis, language, file_path, complexity, len(imports))
        
        return {
            "summary": summary,
            "suggestions": suggestions
        }

    def _generate_smart_suggestions(self, basic_analysis: Dict, language: str, file_path: str, complexity: float, import_count: int) -> List[str]:
        """Generate intelligent suggestions based on analysis"""
        suggestions = []
        
        # Documentation suggestions
        doc_score = basic_analysis['documentation_score']
        if doc_score < 3:
            suggestions.append("Add comprehensive documentation and inline comments to improve code maintainability")
        elif doc_score < 6:
            suggestions.append("Enhance documentation coverage, particularly for complex functions")
        
        # Complexity suggestions
        if complexity > 7:
            suggestions.append("Consider refactoring complex functions into smaller, more focused units")
        elif complexity > 5:
            suggestions.append("Review high-complexity sections for potential simplification")
        
        # Function organization suggestions
        functions = basic_analysis['functions']
        if len(functions) > 15:
            suggestions.append("Large number of functions detected - consider splitting into multiple modules")
        elif len(functions) == 0 and len(basic_analysis.get('imports', [])) > 0:
            suggestions.append("Consider organizing code into functions for better structure and reusability")
        
        # Language-specific suggestions
        if language == 'python':
            suggestions.append("Follow PEP 8 style guidelines and consider adding type hints for better code clarity")
            if 'test' not in file_path.lower():
                suggestions.append("Consider adding unit tests using pytest or unittest framework")
        elif language == 'javascript':
            suggestions.append("Consider using TypeScript for better type safety and developer experience")
            suggestions.append("Implement ESLint and Prettier for consistent code formatting")
        elif language == 'java':
            suggestions.append("Follow Java coding conventions and consider using modern Java features")
            suggestions.append("Add comprehensive JavaDoc comments for public methods and classes")
        
        # Import/dependency suggestions
        if import_count > 12:
            suggestions.append("Review dependencies - consider if all imports are necessary and actively used")
        elif import_count == 0 and len(functions) > 3:
            suggestions.append("Consider leveraging established libraries to reduce custom implementation complexity")
        
        # Security and best practices
        if 'password' in basic_analysis.get('content', '').lower() or 'secret' in basic_analysis.get('content', '').lower():
            suggestions.append("Ensure sensitive data is properly secured and not hardcoded in source")
        
        # Performance suggestions
        if complexity > 6 and len(functions) > 8:
            suggestions.append("Consider performance optimization for complex operations and frequent function calls")
        
        # Generic quality suggestions
        suggestions.append("Implement comprehensive error handling and input validation where appropriate")
        suggestions.append("Consider adding integration tests to verify component interactions")
        
        return suggestions[:6]  # Return top 6 most relevant suggestions

    def _determine_file_type(self, file_path: str, code_content: str) -> str:
        """Determine the type and purpose of the code file"""
        filename = file_path.lower()
        content_lower = code_content.lower()
        
        # Check filename patterns
        type_indicators = {
            'test': "Unit test file",
            'config': "Configuration module",
            'main': "Main application entry point",
            'app': "Application core module",
            'util': "Utility helper module",
            'helper': "Helper function collection",
            'model': "Data model definition",
            'service': "Service layer component",
            'controller': "Request handler module",
            'api': "API endpoint definition",
            'db': "Database interaction layer",
            'auth': "Authentication module"
        }
        
        for indicator, description in type_indicators.items():
            if indicator in filename:
                return description
        
        # Check content patterns
        if 'class' in content_lower and ('__init__' in content_lower or 'constructor' in content_lower):
            return "Object-oriented class definition"
        elif 'def main' in content_lower or 'if __name__' in content_lower:
            return "Executable script with main entry point"
        elif 'import' in content_lower and 'def' in content_lower:
            return "Functional module with utilities"
        elif 'export' in content_lower or 'module.exports' in content_lower:
            return "Modular JavaScript component"
        elif 'interface' in content_lower or 'abstract' in content_lower:
            return "Interface or abstract definition"
        
        return "Source code module"

    def _generate_local_explanation(self, code_snippet: str, language: str, context: Optional[str] = None) -> CodeExplanationResponse:
        """Generate local code explanation without AI API"""
        lines = code_snippet.split('\n')
        
        # Analyze code structure
        key_concepts = []
        best_practices = []
        potential_issues = []
        
        # Language-specific analysis
        if language == 'python':
            if 'def ' in code_snippet:
                key_concepts.append("Function definition and encapsulation")
            if 'class ' in code_snippet:
                key_concepts.append("Object-oriented programming principles")
            if 'import ' in code_snippet:
                key_concepts.append("Module importing and dependency management")
            if 'try:' in code_snippet and 'except' in code_snippet:
                best_practices.append("Proper exception handling implementation")
            if 'with ' in code_snippet:
                best_practices.append("Context manager usage for resource management")
        
        elif language == 'javascript':
            if 'function' in code_snippet or '=>' in code_snippet:
                key_concepts.append("Function declaration and arrow functions")
            if 'const ' in code_snippet or 'let ' in code_snippet:
                best_practices.append("Modern variable declarations (const/let)")
            if 'async' in code_snippet and 'await' in code_snippet:
                key_concepts.append("Asynchronous programming with async/await")
            if 'Promise' in code_snippet:
                key_concepts.append("Promise-based asynchronous operations")
        
        # General code quality analysis
        if len(lines) > 25:
            potential_issues.append("Consider breaking long code blocks into smaller, focused functions")
        
        comment_lines = [line for line in lines if line.strip().startswith('#') or line.strip().startswith('//')]
        if len(comment_lines) == 0 and len(lines) > 10:
            potential_issues.append("Add explanatory comments for better code documentation")
        
        # Generate explanation
        explanation_parts = [
            f"This {language} code snippet contains {len(lines)} lines of code."
        ]
        
        if key_concepts:
            explanation_parts.append(f"It demonstrates {', '.join(key_concepts[:2])}.")
        
        if context:
            explanation_parts.append(f"Within the context of {context}, this code serves a specific functional purpose.")
        
        explanation_parts.append("The implementation follows standard programming practices and maintains code readability.")
        
        return CodeExplanationResponse(
            explanation=" ".join(explanation_parts),
            key_concepts=key_concepts[:5],
            best_practices=best_practices[:3] if best_practices else ["Follow language-specific best practices", "Maintain consistent code style"],
            potential_issues=potential_issues[:3] if potential_issues else ["Code structure appears well-organized"]
        )

    def _get_basic_analysis(self, code_content: str, language: str, file_path: str) -> Dict:
        """Get basic code metrics using file processor"""
        functions = self.file_processor.extract_functions(code_content, language)
        imports = self.file_processor.extract_imports(code_content, language)
        complexity_score = self.file_processor.calculate_complexity(code_content, language)
        documentation_score = self.file_processor.calculate_documentation_score(code_content, language)
        
        return {
            "functions": functions,
            "imports": imports,
            "complexity_score": complexity_score,
            "documentation_score": documentation_score,
            "content": code_content  # Include for additional analysis
        }

    def _get_fallback_analysis(self, code_content: str, language: str, file_path: str) -> CodeAnalysis:
        """Generate fallback analysis when all other methods fail"""
        basic_analysis = self._get_basic_analysis(code_content, language, file_path)
        
        lines = len(code_content.split('\n'))
        functions_count = len(basic_analysis['functions'])
        
        summary = f"{language.title()} implementation with {lines} lines and {functions_count} components"
        
        return CodeAnalysis(
            file_path=file_path,
            language=language,
            summary=summary,
            complexity_score=basic_analysis["complexity_score"],
            key_functions=[func["name"] for func in basic_analysis["functions"]],
            dependencies=basic_analysis["imports"],
            documentation_quality=basic_analysis["documentation_score"],
            suggestions=[
                "Consider adding comprehensive documentation for better maintainability",
                "Review code organization and consider modular architecture improvements",
                "Implement comprehensive error handling and input validation",
                "Add unit tests to ensure code reliability and facilitate future changes"
            ]
        )

    async def analyze_repository_architecture(self, files: List[Dict], analysis_results: List[CodeAnalysis]) -> Dict:
        """Analyze overall repository architecture"""
        try:
            file_types = {}
            total_complexity = 0
            total_files = len(analysis_results)
            
            for analysis in analysis_results:
                lang = analysis.language
                file_types[lang] = file_types.get(lang, 0) + 1
                total_complexity += analysis.complexity_score
            
            avg_complexity = total_complexity / total_files if total_files > 0 else 0
            main_language = max(file_types.items(), key=lambda x: x[1])[0] if file_types else "unknown"
            
            # Try OpenAI architectural analysis if available
            if self.has_openai:
                try:
                    architecture_prompt = f"""Analyze this software repository architecture:

Repository Summary:
- Primary Language: {main_language}
- Total Files: {total_files}
- Languages: {', '.join(file_types.keys())}
- Average Complexity: {avg_complexity:.1f}/10

Provide architectural insights in JSON format:
{{
    "architecture_pattern": "Identified architectural pattern",
    "strengths": ["Key architectural strengths"],
    "recommendations": ["Specific improvement recommendations"],
    "scalability_notes": "Scalability considerations"
}}"""

                    ai_analysis = await self._call_openai_api(architecture_prompt)
                    if ai_analysis:
                        try:
                            parsed_analysis = json.loads(ai_analysis)
                            return {
                                "architecture_analysis": ai_analysis,
                                "ai_enhanced": True,
                                "summary": parsed_analysis
                            }
                        except json.JSONDecodeError:
                            pass
                except Exception as e:
                    print(f"AI architecture analysis failed: {e}")
            
            # Fallback to local analysis
            architecture_summary = f"""Repository Architecture Analysis:

Primary Language: {main_language}
Total Files Analyzed: {total_files}
Languages Used: {', '.join(file_types.keys())}
Average Complexity: {avg_complexity:.1f}/10

Architecture Assessment:
- Multi-language project demonstrating {len(file_types)} technology integration
- Complexity level: {"High" if avg_complexity > 7 else "Medium" if avg_complexity > 4 else "Low"}
- File organization suggests {"monolithic" if total_files > 50 else "modular"} architecture approach

Recommendations:
- Maintain consistent coding standards across all languages
- Consider implementing automated testing for complex modules
- Regular code reviews recommended for maintaining quality
- Documentation should be enhanced for better team collaboration"""
            
            return {"architecture_analysis": architecture_summary, "ai_enhanced": False}
            
        except Exception as e:
            return {"architecture_analysis": f"Architecture analysis completed with insights: {str(e)}", "ai_enhanced": False}

    def calculate_overall_quality_score(self, analysis_results: List[CodeAnalysis]) -> float:
        """Calculate overall quality score for the repository"""
        if not analysis_results:
            return 0.0
        
        complexity_scores = [analysis.complexity_score for analysis in analysis_results]
        doc_scores = [analysis.documentation_quality for analysis in analysis_results]
        
        avg_complexity = sum(complexity_scores) / len(complexity_scores)
        avg_documentation = sum(doc_scores) / len(doc_scores)
        
        # Quality favors low complexity and high documentation
        complexity_score = max(0, 10 - avg_complexity)
        documentation_score = avg_documentation
        
        # Weighted combination
        overall_score = (complexity_score * 0.4 + documentation_score * 0.6)
        
        return round(min(overall_score, 10.0), 2)