from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import asyncio
from typing import Dict, Any

from .config import settings
from .models import (
    RepoAnalysisRequest, RepoAnalysisResponse,
    CodeExplanationRequest, CodeExplanationResponse,
    QualityMetrics, SearchRequest, SearchResult
)
from .services.github_service import GitHubService
from .services.code_analyzer import CodeAnalyzer
from .services.doc_generator import DocumentationGenerator
from .services.vector_store import VectorStore
from .services.mcp_service import mcp_service

app = FastAPI(
    title="Smart Code Documentation Generator",
    description="AI-powered code documentation generator with GitHub integration and MCP coordination",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

github_service = GitHubService()
code_analyzer = CodeAnalyzer()
doc_generator = DocumentationGenerator()
vector_store = VectorStore()

analysis_cache: Dict[str, Any] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        await mcp_service.initialize()
        print("🚀 MCP Service initialized")
    except Exception as e:
        print(f"⚠️ MCP Service optional - continuing: {e}")

@app.on_event("shutdown") 
async def shutdown_event():
    """Clean up services on shutdown"""
    await mcp_service.close()

@app.get("/")
async def root():
    return {
        "message": "Smart Code Documentation Generator API", 
        "version": "1.0.0",
        "features": [
            "Repository Analysis",
            "Code Quality Metrics", 
            "Documentation Generation",
            "Semantic Code Search",
            "MCP Coordination"
        ],
        "endpoints": {
            "analysis": "/analyze-repo",
            "mcp_analysis": "/analyze-repo-mcp", 
            "code_explanation": "/explain-code",
            "search": "/search-code",
            "capabilities": "/mcp-capabilities"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "timestamp": time.time(),
        "services": {
            "github_service": "ready",
            "code_analyzer": "ready",
            "doc_generator": "ready",
            "vector_store": "ready",
            "mcp_service": "ready" if mcp_service.is_initialized else "unavailable"
        },
        "features": {
            "direct_analysis": "available",
            "mcp_coordination": "available" if mcp_service.is_initialized else "unavailable",
            "semantic_search": "available",
            "documentation_generation": "available"
        }
    }

@app.post("/analyze-repo", response_model=RepoAnalysisResponse)
async def analyze_repository(request: RepoAnalysisRequest):
    """Analyze repository using direct service calls (production approach)"""
    try:
        start_time = time.time()
        
        repo_key = f"{request.repo_url}:{request.branch}"
        if repo_key in analysis_cache:
            cached_result = analysis_cache[repo_key]
            cached_result["processing_time"] = time.time() - start_time
            cached_result["cache_hit"] = True
            return cached_result
        
        repo_info = await github_service.get_repo_info(request.repo_url)
        files = await github_service.get_repo_files(
            request.repo_url, 
            request.branch,
            request.include_patterns,
            request.exclude_patterns
        )
        
        analysis_results = []
        for file_info in files:
            if file_info.content:
                analysis = await code_analyzer.analyze_code(
                    file_info.content, 
                    file_info.language, 
                    file_info.path
                )
                analysis_results.append(analysis)
                
                await vector_store.add_document(
                    file_info.path,
                    file_info.content,
                    {"language": file_info.language, "repo": repo_info["name"]}
                )
        
        documentation = await doc_generator.generate_documentation(
            repo_info, files, analysis_results
        )
        
        processing_time = time.time() - start_time
        
        result = RepoAnalysisResponse(
            repo_info=repo_info,
            files=files,
            analysis=analysis_results,
            documentation=documentation,
            processing_time=processing_time
        )
        
        analysis_cache[repo_key] = result.dict()
        analysis_cache[repo_key]["cache_hit"] = False
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/analyze-repo-mcp")
async def analyze_repository_mcp(request: RepoAnalysisRequest):
    """Analyze repository using MCP coordination (advanced approach)"""
    try:
        start_time = time.time()
        
        # Use MCP for coordinated analysis
        mcp_result = await mcp_service.analyze_repository_via_mcp(
            request.repo_url, 
            request.branch
        )
        
        # For demo, also run actual analysis but show MCP coordination
        try:
            # Get actual analysis for comparison
            repo_info = await github_service.get_repo_info(request.repo_url)
            files = await github_service.get_repo_files(
                request.repo_url, 
                request.branch,
                request.include_patterns,
                request.exclude_patterns
            )
            
            # Limit analysis for demo
            analysis_results = []
            for file_info in files[:5]:  # Analyze first 5 files
                if file_info.content:
                    analysis = await code_analyzer.analyze_code(
                        file_info.content, 
                        file_info.language, 
                        file_info.path
                    )
                    analysis_results.append(analysis)
            
            documentation = await doc_generator.generate_documentation(
                repo_info, files, analysis_results
            )
            
            processing_time = time.time() - start_time
            
            return {
                "mcp_coordination": mcp_result,
                "actual_analysis": {
                    "repo_info": repo_info,
                    "files_analyzed": len(analysis_results),
                    "analysis": [a.dict() for a in analysis_results],
                    "documentation": documentation.dict(),
                    "processing_time": processing_time
                },
                "architecture": "mcp_coordinated",
                "benefits": [
                    "Context sharing between analysis tools",
                    "Workflow orchestration via MCP protocol",
                    "Standardized tool coordination",
                    "Enhanced error recovery"
                ]
            }
            
        except Exception as analysis_error:
            # Return MCP result even if actual analysis fails
            return {
                "mcp_coordination": mcp_result,
                "analysis_note": f"MCP coordination successful, analysis error: {str(analysis_error)}",
                "architecture": "mcp_coordinated"
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MCP analysis failed: {str(e)}")

@app.post("/explain-code", response_model=CodeExplanationResponse)
async def explain_code(request: CodeExplanationRequest):
    """Explain code using direct analysis"""
    try:
        explanation = await code_analyzer.explain_code(
            request.code_snippet,
            request.language,
            request.context
        )
        return explanation
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code explanation failed: {str(e)}")

@app.post("/explain-code-mcp")
async def explain_code_mcp(request: CodeExplanationRequest):
    """Explain code using MCP coordination"""
    try:
        mcp_result = await mcp_service.explain_code_via_mcp(
            request.code_snippet,
            request.language, 
            request.context
        )
        
        # Also get direct explanation for comparison
        direct_explanation = await code_analyzer.explain_code(
            request.code_snippet,
            request.language,
            request.context
        )
        
        return {
            "mcp_coordination": mcp_result,
            "direct_explanation": direct_explanation.dict(),
            "architecture": "mcp_coordinated",
            "benefits": ["Context-aware explanations", "Cross-tool coordination"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MCP explanation failed: {str(e)}")

@app.post("/search-code")
async def search_code(request: SearchRequest):
    """Search code using vector similarity"""
    try:
        results = await vector_store.search(request.query, request.limit)
        return {"results": results, "architecture": "direct_vector_search"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/search-code-mcp")
async def search_code_mcp(request: SearchRequest):
    """Search code using MCP coordination"""
    try:
        mcp_result = await mcp_service.search_code_via_mcp(
            request.query,
            request.repo_name,
            request.limit
        )
        
        # Also get direct search for comparison
        direct_results = await vector_store.search(request.query, request.limit)
        
        return {
            "mcp_coordination": mcp_result,
            "direct_search": {"results": direct_results},
            "architecture": "mcp_coordinated",
            "benefits": ["Context-enhanced search", "Project-aware ranking"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MCP search failed: {str(e)}")

@app.get("/quality-metrics/{repo_name}")
async def get_quality_metrics(repo_name: str):
    """Get quality metrics for analyzed repository"""
    try:
        if repo_name not in analysis_cache:
            raise HTTPException(status_code=404, detail="Repository not analyzed yet")
        
        cached_data = analysis_cache[repo_name]
        metrics = doc_generator.calculate_quality_metrics(cached_data["analysis"])
        return {
            "metrics": metrics,
            "architecture": "direct_calculation"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quality metrics calculation failed: {str(e)}")

@app.get("/mcp-capabilities")
async def get_mcp_capabilities():
    """Show MCP coordination capabilities and available tools"""
    try:
        capabilities = await mcp_service.list_mcp_capabilities()
        return capabilities
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get MCP capabilities: {str(e)}")

@app.get("/supported-languages")
async def get_supported_languages():
    """Get list of supported programming languages"""
    return {
        "languages": settings.SUPPORTED_LANGUAGES,
        "total_count": len(settings.SUPPORTED_LANGUAGES),
        "categories": {
            "compiled": ["java", "cpp", "c", "csharp", "go", "rust"],
            "interpreted": ["python", "javascript", "php", "ruby"],
            "web": ["html", "css", "javascript", "typescript"],
            "data": ["json", "yaml", "xml", "toml"],
            "documentation": ["markdown"]
        }
    }

@app.get("/architecture-info")
async def get_architecture_info():
    """Get information about the system architecture"""
    return {
        "system_architecture": {
            "approach": "hybrid",
            "description": "Dual architecture supporting both direct service calls and MCP coordination"
        },
        "direct_services": {
            "description": "Fast, reliable service calls for production workloads",
            "benefits": ["High performance", "Easy debugging", "Minimal latency"],
            "endpoints": ["/analyze-repo", "/explain-code", "/search-code"]
        },
        "mcp_coordination": {
            "description": "Model Context Protocol for advanced tool coordination",
            "benefits": ["Context sharing", "Workflow orchestration", "Standardized protocols"],
            "endpoints": ["/analyze-repo-mcp", "/explain-code-mcp", "/search-code-mcp"]
        },
        "tech_stack": {
            "backend": ["FastAPI", "Python", "LangChain", "ChromaDB"],
            "coordination": ["MCP", "Tool orchestration"],
            "integration": ["GitHub API", "Vector search"],
            "frontend": ["React", "Monaco Editor", "Modern UI"]
        },
        "capabilities": {
            "repository_analysis": True,
            "code_explanation": True,
            "semantic_search": True,
            "documentation_generation": True,
            "quality_metrics": True,
            "mcp_coordination": mcp_service.is_initialized
        }
    }

@app.delete("/cache/{repo_name}")
async def clear_cache(repo_name: str):
    """Clear analysis cache for a specific repository"""
    keys_to_remove = [key for key in analysis_cache.keys() if repo_name in key]
    for key in keys_to_remove:
        del analysis_cache[key]
    return {
        "message": f"Cache cleared for {repo_name}",
        "keys_removed": len(keys_to_remove)
    }

@app.delete("/cache")
async def clear_all_cache():
    """Clear all analysis cache"""
    cache_size = len(analysis_cache)
    analysis_cache.clear()
    return {
        "message": "All cache cleared",
        "entries_removed": cache_size
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for better error responses"""
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal server error: {str(exc)}",
            "type": "server_error",
            "suggestion": "Please check the logs and try again"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)