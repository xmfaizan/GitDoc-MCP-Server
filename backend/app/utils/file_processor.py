import os
import re
from typing import List, Dict, Optional, Tuple
from ..config import settings

class FileProcessor:
    def __init__(self):
        self.supported_languages = settings.SUPPORTED_LANGUAGES

    def extract_functions(self, content: str, language: str) -> List[Dict[str, str]]:
        functions = []
        
        patterns = {
            "python": [
                r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\):',
                r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\([^)]*\))?:'
            ],
            "javascript": [
                r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                r'const\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>',
                r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(?:async\s+)?function\s*\(',
                r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*{'
            ],
            "typescript": [
                r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                r'const\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>',
                r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(?:async\s+)?function\s*\(',
                r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*{'
            ],
            "java": [
                r'(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?(?:abstract\s+)?(?:synchronized\s+)?[a-zA-Z<>\[\]]+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                r'(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?(?:abstract\s+)?class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*'
            ],
            "cpp": [
                r'(?:[a-zA-Z_][a-zA-Z0-9_]*\s+)+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*{',
                r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*'
            ],
            "csharp": [
                r'(?:public|private|protected|internal)?\s*(?:static\s+)?(?:virtual\s+)?(?:override\s+)?(?:async\s+)?[a-zA-Z<>\[\]]+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                r'(?:public|private|protected|internal)?\s*(?:static\s+)?(?:abstract\s+)?(?:sealed\s+)?class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*'
            ],
            "go": [
                r'func\s+(?:\([^)]*\)\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                r'type\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+struct\s*{'
            ],
            "rust": [
                r'fn\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                r'struct\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*',
                r'impl\s+(?:[^{]*\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*{'
            ],
            "php": [
                r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*'
            ],
            "ruby": [
                r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            ],
            "swift": [
                r'func\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*',
                r'struct\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*'
            ]
        }
        
        if language in patterns:
            for pattern in patterns[language]:
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    functions.append({
                        "name": match.group(1),
                        "line": content[:match.start()].count('\n') + 1,
                        "type": "class" if "class" in pattern.lower() else "function"
                    })
        
        return functions

    def extract_imports(self, content: str, language: str) -> List[str]:
        imports = []
        
        patterns = {
            "python": [
                r'import\s+([a-zA-Z_][a-zA-Z0-9_.]*)',
                r'from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import'
            ],
            "javascript": [
                r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
                r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
            ],
            "typescript": [
                r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
                r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
            ],
            "java": [
                r'import\s+([a-zA-Z_][a-zA-Z0-9_.]*);'
            ],
            "cpp": [
                r'#include\s*[<"]([^>"]+)[>"]'
            ],
            "csharp": [
                r'using\s+([a-zA-Z_][a-zA-Z0-9_.]*);'
            ],
            "go": [
                r'import\s+[\'"]([^\'"]+)[\'"]'
            ],
            "rust": [
                r'use\s+([a-zA-Z_][a-zA-Z0-9_::]*);'
            ],
            "php": [
                r'use\s+([a-zA-Z_][a-zA-Z0-9_\\]*);',
                r'require_once\s+[\'"]([^\'"]+)[\'"]'
            ]
        }
        
        if language in patterns:
            for pattern in patterns[language]:
                matches = re.findall(pattern, content)
                imports.extend(matches)
        
        return list(set(imports))

    def calculate_complexity(self, content: str, language: str) -> float:
        complexity_indicators = {
            "loops": [r'\bfor\b', r'\bwhile\b', r'\bdo\b'],
            "conditionals": [r'\bif\b', r'\belse\b', r'\belif\b', r'\bswitch\b', r'\bcase\b'],
            "functions": [r'\bdef\b', r'\bfunction\b', r'\bfunc\b'],
            "classes": [r'\bclass\b'],
            "exceptions": [r'\btry\b', r'\bcatch\b', r'\bexcept\b', r'\bfinally\b'],
            "async": [r'\basync\b', r'\bawait\b', r'\bPromise\b']
        }
        
        total_score = 0
        lines = content.split('\n')
        
        for category, patterns in complexity_indicators.items():
            count = 0
            for pattern in patterns:
                count += len(re.findall(pattern, content, re.IGNORECASE))
            
            if category == "loops":
                total_score += count * 2
            elif category == "conditionals":
                total_score += count * 1
            elif category == "functions":
                total_score += count * 0.5
            elif category == "classes":
                total_score += count * 0.5
            elif category == "exceptions":
                total_score += count * 1.5
            elif category == "async":
                total_score += count * 1.5
        
        lines_of_code = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        
        if lines_of_code == 0:
            return 0.0
        
        complexity = min(total_score / lines_of_code * 10, 10.0)
        return round(complexity, 2)

    def extract_comments(self, content: str, language: str) -> List[Dict[str, any]]:
        comments = []
        
        comment_patterns = {
            "python": [r'#\s*(.+)$', r'"""(.*?)"""', r"'''(.*?)'''"],
            "javascript": [r'//\s*(.+)$', r'/\*(.*?)\*/'],
            "typescript": [r'//\s*(.+)$', r'/\*(.*?)\*/'],
            "java": [r'//\s*(.+)$', r'/\*(.*?)\*/'],
            "cpp": [r'//\s*(.+)$', r'/\*(.*?)\*/'],
            "csharp": [r'//\s*(.+)$', r'/\*(.*?)\*/'],
            "go": [r'//\s*(.+)$', r'/\*(.*?)\*/'],
            "rust": [r'//\s*(.+)$', r'/\*(.*?)\*/'],
            "php": [r'//\s*(.+)$', r'#\s*(.+)$', r'/\*(.*?)\*/'],
            "ruby": [r'#\s*(.+)$'],
            "swift": [r'//\s*(.+)$', r'/\*(.*?)\*/']
        }
        
        if language in comment_patterns:
            for pattern in comment_patterns[language]:
                matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
                for match in matches:
                    comment_text = match.group(1).strip()
                    if comment_text:
                        line_number = content[:match.start()].count('\n') + 1
                        comments.append({
                            "text": comment_text,
                            "line": line_number,
                            "type": "block" if "/*" in pattern or '"""' in pattern else "inline"
                        })
        
        return comments

    def calculate_documentation_score(self, content: str, language: str) -> float:
        lines = content.split('\n')
        total_lines = len(lines)
        code_lines = len([line for line in lines if line.strip() and not self._is_comment_line(line, language)])
        comment_lines = total_lines - code_lines
        
        if code_lines == 0:
            return 0.0
        
        functions = self.extract_functions(content, language)
        documented_functions = 0
        
        for func in functions:
            func_line = func["line"]
            if func_line < len(lines):
                before_func = '\n'.join(lines[max(0, func_line-5):func_line-1])
                after_func = '\n'.join(lines[func_line:min(len(lines), func_line+3)])
                
                if self._has_docstring(before_func + after_func, language):
                    documented_functions += 1
        
        function_doc_ratio = documented_functions / len(functions) if functions else 0
        comment_ratio = min(comment_lines / code_lines, 0.5) * 2
        
        score = (function_doc_ratio * 0.7 + comment_ratio * 0.3) * 10
        return round(min(score, 10.0), 2)

    def _is_comment_line(self, line: str, language: str) -> bool:
        line = line.strip()
        if not line:
            return True
        
        comment_starters = {
            "python": ["#", '"""', "'''"],
            "javascript": ["//", "/*"],
            "typescript": ["//", "/*"],
            "java": ["//", "/*"],
            "cpp": ["//", "/*"],
            "csharp": ["//", "/*"],
            "go": ["//", "/*"],
            "rust": ["//", "/*"],
            "php": ["//", "#", "/*"],
            "ruby": ["#"],
            "swift": ["//", "/*"]
        }
        
        if language in comment_starters:
            return any(line.startswith(starter) for starter in comment_starters[language])
        
        return False

    def _has_docstring(self, content: str, language: str) -> bool:
        docstring_patterns = {
            "python": [r'""".*?"""', r"'''.*?'''"],
            "javascript": [r'/\*\*.*?\*/', r'//.*?@param', r'//.*?@returns'],
            "typescript": [r'/\*\*.*?\*/', r'//.*?@param', r'//.*?@returns'],
            "java": [r'/\*\*.*?\*/'],
            "cpp": [r'/\*\*.*?\*/'],
            "csharp": [r'///.*?', r'/\*\*.*?\*/'],
            "go": [r'//.*?'],
            "rust": [r'///.*?', r'//!.*?'],
            "php": [r'/\*\*.*?\*/'],
            "swift": [r'///.*?', r'/\*\*.*?\*/']
        }
        
        if language in docstring_patterns:
            for pattern in docstring_patterns[language]:
                if re.search(pattern, content, re.DOTALL):
                    return True
        
        return False