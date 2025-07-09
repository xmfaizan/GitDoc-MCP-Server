import React, { useState, useEffect } from "react";
import {
  Github,
  Sparkles,
  AlertCircle,
  CheckCircle,
  RefreshCw,
  Zap,
  FileText,
  Search,
} from "lucide-react";

import RepoInput from "./components/RepoInput";
import CodeExplorer from "./components/CodeExplorer";
import DocumentationView from "./components/DocumentationView";
import QualityScore from "./components/QualityScore";
import { apiService, formatError } from "./services/api";
import "./App.css";

function App() {
  const [analysisData, setAnalysisData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentRepo, setCurrentRepo] = useState(null);
  const [searchResults, setSearchResults] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [backendHealth, setBackendHealth] = useState("checking");

  useEffect(() => {
    checkBackendHealth();
  }, []);

  const checkBackendHealth = async () => {
    try {
      await apiService.healthCheck();
      setBackendHealth("healthy");
    } catch (error) {
      setBackendHealth("error");
    }
  };

  const handleAnalyzeRepo = async (repoData) => {
    setIsLoading(true);
    setError(null);
    setAnalysisData(null);
    setSearchResults(null);
    setCurrentRepo(repoData);

    try {
      const result = await apiService.analyzeRepository(repoData);
      setAnalysisData(result);
      setActiveTab("overview");
    } catch (err) {
      setError(formatError(err));
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = async (query) => {
    if (!currentRepo) return;

    try {
      const results = await apiService.searchCode({
        query,
        repo_name: currentRepo.repo_name,
        limit: 10,
      });
      setSearchResults(results);
    } catch (err) {
      console.error("Search failed:", err);
    }
  };

  const clearAnalysis = () => {
    setAnalysisData(null);
    setError(null);
    setCurrentRepo(null);
    setSearchResults(null);
    setActiveTab("overview");
  };

  const tabs = [
    { id: "overview", label: "Overview", icon: FileText },
    { id: "explorer", label: "Code Explorer", icon: Search },
    { id: "documentation", label: "Documentation", icon: FileText },
    { id: "quality", label: "Quality Score", icon: Zap },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <Github className="text-blue-600" size={32} />
                <Sparkles className="text-purple-600" size={24} />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  Smart Code Documentation
                </h1>
                <p className="text-sm text-gray-500">
                  AI-powered repository analysis
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div
                className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
                  backendHealth === "healthy"
                    ? "bg-green-100 text-green-700"
                    : backendHealth === "error"
                    ? "bg-red-100 text-red-700"
                    : "bg-yellow-100 text-yellow-700"
                }`}
              >
                {backendHealth === "healthy" ? (
                  <CheckCircle size={16} />
                ) : backendHealth === "error" ? (
                  <AlertCircle size={16} />
                ) : (
                  <RefreshCw size={16} className="animate-spin" />
                )}
                {backendHealth === "healthy"
                  ? "Connected"
                  : backendHealth === "error"
                  ? "Disconnected"
                  : "Connecting..."}
              </div>

              {analysisData && (
                <button
                  onClick={clearAnalysis}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  New Analysis
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Backend Health Warning */}
        {backendHealth === "error" && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center gap-2">
              <AlertCircle className="text-red-600" size={20} />
              <div>
                <h3 className="font-semibold text-red-800">
                  Backend Connection Error
                </h3>
                <p className="text-red-700 text-sm">
                  Cannot connect to the backend API. Please ensure the backend
                  server is running on port 8000.
                </p>
                <button
                  onClick={checkBackendHealth}
                  className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
                >
                  Retry Connection
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Repository Input */}
        {!analysisData && !isLoading && (
          <RepoInput onAnalyze={handleAnalyzeRepo} isLoading={isLoading} />
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="bg-white rounded-xl shadow-lg p-8 text-center">
            <div className="flex flex-col items-center space-y-4">
              <div className="relative">
                <div className="spinner"></div>
                <Github
                  className="absolute inset-0 m-auto text-blue-600"
                  size={24}
                />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-800">
                  Analyzing Repository
                </h3>
                <p className="text-gray-600">This may take a few moments...</p>
              </div>
              <div className="w-full max-w-md bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full animate-pulse"
                  style={{ width: "70%" }}
                ></div>
              </div>
              <div className="text-sm text-gray-500 space-y-1">
                <div>• Fetching repository files...</div>
                <div>• Analyzing code structure...</div>
                <div>• Generating documentation...</div>
                <div>• Calculating quality metrics...</div>
              </div>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-white rounded-xl shadow-lg p-8">
            <div className="text-center">
              <AlertCircle className="mx-auto mb-4 text-red-500" size={48} />
              <h3 className="text-lg font-semibold text-gray-800 mb-2">
                Analysis Failed
              </h3>
              <p className="text-gray-600 mb-4">{error}</p>
              <button
                onClick={clearAnalysis}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        )}

        {/* Analysis Results */}
        {analysisData && (
          <div className="space-y-8">
            {/* Repository Info Banner */}
            <div className="gradient-blue-purple text-white rounded-xl p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold mb-2">
                    {analysisData.repo_info.name}
                  </h2>
                  <p className="text-blue-100 mb-3">
                    {analysisData.repo_info.description}
                  </p>
                  <div className="flex items-center gap-6 text-sm text-blue-100">
                    <span>
                      ⭐ {analysisData.repo_info.stars?.toLocaleString() || 0}{" "}
                      stars
                    </span>
                    <span>
                      📁 {analysisData.files?.length || 0} files analyzed
                    </span>
                    <span>🔧 {analysisData.repo_info.language}</span>
                    <span>
                      ⏱️ {analysisData.processing_time?.toFixed(1)}s processing
                      time
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-3xl font-bold">
                    {analysisData.documentation?.quality_score?.toFixed(1) ||
                      "N/A"}
                  </div>
                  <div className="text-blue-100">Quality Score</div>
                </div>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="border-b border-gray-200">
                <div className="flex overflow-x-auto">
                  {tabs.map((tab) => {
                    const Icon = tab.icon;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`tab ${
                          activeTab === tab.id ? "active" : ""
                        }`}
                      >
                        <Icon size={18} />
                        {tab.label}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Tab Content */}
            <div>
              {activeTab === "overview" && (
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: "2rem",
                    alignItems: "start",
                  }}
                >
                  <DocumentationView
                    documentation={analysisData.documentation}
                    repoInfo={analysisData.repo_info}
                  />
                  <QualityScore
                    analysisData={analysisData}
                    documentation={analysisData.documentation}
                  />
                </div>
              )}

              {activeTab === "explorer" && (
                <div className="space-y-6">
                  <CodeExplorer
                    analysisData={analysisData}
                    onSearch={handleSearch}
                  />

                  {searchResults && (
                    <div className="bg-white rounded-xl shadow-lg p-6">
                      <h3 className="text-xl font-bold text-gray-800 mb-4">
                        Search Results
                      </h3>
                      {searchResults.results?.length > 0 ? (
                        <div className="space-y-4">
                          {searchResults.results.map((result, index) => (
                            <div
                              key={index}
                              className="border border-gray-200 rounded-lg p-4"
                            >
                              <div className="flex items-center justify-between mb-2">
                                <span className="font-mono text-sm text-blue-600">
                                  {result.file_path}
                                </span>
                                <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                                  {(result.relevance_score * 100).toFixed(0)}%
                                  match
                                </span>
                              </div>
                              <pre className="bg-gray-50 p-3 rounded text-sm overflow-x-auto">
                                <code>{result.content}</code>
                              </pre>
                              <p className="text-xs text-gray-500 mt-2">
                                {result.context}
                              </p>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-gray-500">
                          No results found for your search query.
                        </p>
                      )}
                    </div>
                  )}
                </div>
              )}

              {activeTab === "documentation" && (
                <DocumentationView
                  documentation={analysisData.documentation}
                  repoInfo={analysisData.repo_info}
                />
              )}

              {activeTab === "quality" && (
                <QualityScore
                  analysisData={analysisData}
                  documentation={analysisData.documentation}
                />
              )}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-gray-500">
            <div className="flex items-center justify-center gap-2 mb-2">
              <Github size={20} />
              <span className="font-semibold">
                Smart Code Documentation Generator
              </span>
            </div>
            <p className="text-sm">
              Powered by AI • Built with FastAPI + React • LangChain + ChromaDB
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
