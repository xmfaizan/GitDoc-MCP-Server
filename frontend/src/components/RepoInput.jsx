import React, { useState } from "react";
import { Github, Search, AlertCircle, CheckCircle } from "lucide-react";
import { validateGitHubUrl, extractRepoInfo } from "../services/api";

const RepoInput = ({ onAnalyze, isLoading }) => {
  const [repoUrl, setRepoUrl] = useState("");
  const [branch, setBranch] = useState("main");
  const [isValid, setIsValid] = useState(false);
  const [showValidation, setShowValidation] = useState(false);

  const handleUrlChange = (e) => {
    const url = e.target.value;
    setRepoUrl(url);
    setIsValid(validateGitHubUrl(url));
    setShowValidation(url.length > 0);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (isValid && !isLoading) {
      const repoInfo = extractRepoInfo(repoUrl);
      onAnalyze({
        repo_url: repoUrl.trim(),
        branch: branch || "main",
        repo_name: repoInfo ? `${repoInfo.owner}/${repoInfo.repo}` : "unknown",
      });
    }
  };

  const exampleRepos = [
    "https://github.com/microsoft/vscode",
    "https://github.com/facebook/react",
    "https://github.com/tensorflow/tensorflow",
    "https://github.com/pallets/flask",
  ];

  const handleExampleClick = (url) => {
    setRepoUrl(url);
    setIsValid(true);
    setShowValidation(true);
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
      <div className="flex items-center gap-3 mb-6">
        <Github className="text-blue-600" size={28} />
        <h2 className="text-2xl font-bold text-gray-800">
          Repository Analysis
        </h2>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label
            htmlFor="repo-url"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            GitHub Repository URL
          </label>
          <div className="relative">
            <input
              id="repo-url"
              type="url"
              value={repoUrl}
              onChange={handleUrlChange}
              placeholder="https://github.com/owner/repository"
              className={`w-full px-4 py-3 pr-12 rounded-lg border-2 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                showValidation
                  ? isValid
                    ? "border-green-300 bg-green-50"
                    : "border-red-300 bg-red-50"
                  : "border-gray-300"
              }`}
              disabled={isLoading}
            />
            {showValidation && (
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                {isValid ? (
                  <CheckCircle className="text-green-500" size={20} />
                ) : (
                  <AlertCircle className="text-red-500" size={20} />
                )}
              </div>
            )}
          </div>
          {showValidation && !isValid && (
            <p className="mt-2 text-sm text-red-600">
              Please enter a valid GitHub repository URL
            </p>
          )}
        </div>

        <div>
          <label
            htmlFor="branch"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Branch (optional)
          </label>
          <input
            id="branch"
            type="text"
            value={branch}
            onChange={(e) => setBranch(e.target.value)}
            placeholder="main"
            className="w-full px-4 py-3 rounded-lg border-2 border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            disabled={isLoading}
          />
        </div>

        <button
          type="submit"
          disabled={!isValid || isLoading}
          className={`w-full flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-medium transition-all ${
            isValid && !isLoading
              ? "bg-blue-600 hover:bg-blue-700 text-white shadow-md hover:shadow-lg transform hover:-translate-y-0.5"
              : "bg-gray-300 text-gray-500 cursor-not-allowed"
          }`}
        >
          {isLoading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              Analyzing Repository...
            </>
          ) : (
            <>
              <Search size={20} />
              Analyze Repository
            </>
          )}
        </button>
      </form>

      <div className="mt-8">
        <h3 className="text-lg font-semibold text-gray-700 mb-4">
          Try Example Repositories
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {exampleRepos.map((url, index) => (
            <button
              key={index}
              onClick={() => handleExampleClick(url)}
              disabled={isLoading}
              className="text-left p-3 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div className="flex items-center gap-2">
                <Github size={16} className="text-gray-500" />
                <span className="text-sm font-mono text-blue-600">
                  {url.split("/").slice(-2).join("/")}
                </span>
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        <h4 className="font-semibold text-blue-800 mb-2">What happens next?</h4>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• Repository files are fetched and analyzed</li>
          <li>• AI analyzes code complexity and patterns</li>
          <li>• Documentation is automatically generated</li>
          <li>• Interactive code explorer is created</li>
          <li>• Quality metrics are calculated</li>
        </ul>
      </div>
    </div>
  );
};

export default RepoInput;
