import React, { useState, useCallback } from "react";
import { Editor } from "@monaco-editor/react";
import {
  Folder,
  File,
  ChevronRight,
  ChevronDown,
  Search,
  MessageSquare,
  Zap,
  Code,
  Eye,
} from "lucide-react";
import { apiService } from "../services/api";

const CodeExplorer = ({ analysisData, onSearch }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [expandedFolders, setExpandedFolders] = useState(new Set(["root"]));
  const [explanation, setExplanation] = useState(null);
  const [isExplaining, setIsExplaining] = useState(false);
  const [selectedCode, setSelectedCode] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  const fileTree = buildFileTree(analysisData?.files || []);

  const toggleFolder = (path) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpandedFolders(newExpanded);
  };

  const selectFile = (file) => {
    setSelectedFile(file);
    setExplanation(null);
    setSelectedCode("");
  };

  const handleEditorSelectionChange = useCallback((editor) => {
    const selection = editor.getSelection();
    const model = editor.getModel();
    if (selection && model && !selection.isEmpty()) {
      const selectedText = model.getValueInRange(selection);
      setSelectedCode(selectedText);
    } else {
      setSelectedCode("");
    }
  }, []);

  const explainCode = async () => {
    if (!selectedCode || !selectedFile) return;

    setIsExplaining(true);
    try {
      const response = await apiService.explainCode({
        file_path: selectedFile.path,
        code_snippet: selectedCode,
        language: selectedFile.language,
        context: `From file ${selectedFile.path} in repository analysis`,
      });
      setExplanation(response);
    } catch (error) {
      console.error("Failed to explain code:", error);
      setExplanation({
        explanation: "Failed to generate explanation. Please try again.",
        key_concepts: [],
        best_practices: [],
        potential_issues: [],
      });
    } finally {
      setIsExplaining(false);
    }
  };

  const handleSearch = () => {
    if (searchQuery.trim() && onSearch) {
      onSearch(searchQuery.trim());
    }
  };

  const getLanguageForMonaco = (language) => {
    const languageMap = {
      javascript: "javascript",
      typescript: "typescript",
      python: "python",
      java: "java",
      cpp: "cpp",
      c: "c",
      csharp: "csharp",
      go: "go",
      rust: "rust",
      php: "php",
      ruby: "ruby",
      swift: "swift",
      kotlin: "kotlin",
      scala: "scala",
      json: "json",
      yaml: "yaml",
      xml: "xml",
      html: "html",
      css: "css",
      markdown: "markdown",
    };
    return languageMap[language] || "plaintext";
  };

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden">
      <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Code className="text-blue-600" size={24} />
            <h3 className="text-xl font-bold text-gray-800">Code Explorer</h3>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <input
                type="text"
                placeholder="Search code..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleSearch()}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={handleSearch}
                className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Search size={16} />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="flex h-96">
        <div className="w-1/3 border-r border-gray-200 overflow-y-auto">
          <div className="p-4">
            <h4 className="font-semibold text-gray-700 mb-3">File Structure</h4>
            <FileTreeNode
              node={fileTree}
              path="root"
              expandedFolders={expandedFolders}
              onToggleFolder={toggleFolder}
              onSelectFile={selectFile}
              selectedFile={selectedFile}
            />
          </div>
        </div>

        <div className="flex-1 flex flex-col">
          {selectedFile ? (
            <>
              <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <File size={16} className="text-gray-500" />
                  <span className="font-mono text-sm">{selectedFile.path}</span>
                  <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                    {selectedFile.language}
                  </span>
                </div>
                {selectedCode && (
                  <button
                    onClick={explainCode}
                    disabled={isExplaining}
                    className="flex items-center gap-2 px-3 py-1 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
                  >
                    {isExplaining ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    ) : (
                      <Zap size={16} />
                    )}
                    Explain Selected
                  </button>
                )}
              </div>

              <div className="flex-1">
                <Editor
                  height="100%"
                  language={getLanguageForMonaco(selectedFile.language)}
                  value={
                    selectedFile.content || "// File content not available"
                  }
                  theme="vs-dark"
                  options={{
                    readOnly: true,
                    minimap: { enabled: true },
                    fontSize: 14,
                    lineNumbers: "on",
                    roundedSelection: false,
                    scrollBeyondLastLine: false,
                    automaticLayout: true,
                  }}
                  onMount={(editor) => {
                    editor.onDidChangeCursorSelection(() => {
                      handleEditorSelectionChange(editor);
                    });
                  }}
                />
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-500">
              <div className="text-center">
                <Eye size={48} className="mx-auto mb-4 text-gray-300" />
                <p className="text-lg font-medium">
                  Select a file to view its contents
                </p>
                <p className="text-sm">
                  Choose any file from the tree to explore the code
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {explanation && (
        <div className="border-t border-gray-200 bg-gray-50 p-4">
          <div className="flex items-center gap-2 mb-3">
            <MessageSquare className="text-purple-600" size={20} />
            <h4 className="font-semibold text-gray-800">AI Code Explanation</h4>
          </div>

          <div className="bg-white rounded-lg p-4 space-y-4">
            <div>
              <h5 className="font-medium text-gray-700 mb-2">Explanation</h5>
              <p className="text-gray-600 text-sm leading-relaxed">
                {explanation.explanation}
              </p>
            </div>

            {explanation.key_concepts?.length > 0 && (
              <div>
                <h5 className="font-medium text-gray-700 mb-2">Key Concepts</h5>
                <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                  {explanation.key_concepts.map((concept, index) => (
                    <li key={index}>{concept}</li>
                  ))}
                </ul>
              </div>
            )}

            {explanation.best_practices?.length > 0 && (
              <div>
                <h5 className="font-medium text-green-700 mb-2">
                  Best Practices
                </h5>
                <ul className="list-disc list-inside text-sm text-green-600 space-y-1">
                  {explanation.best_practices.map((practice, index) => (
                    <li key={index}>{practice}</li>
                  ))}
                </ul>
              </div>
            )}

            {explanation.potential_issues?.length > 0 && (
              <div>
                <h5 className="font-medium text-orange-700 mb-2">
                  Potential Issues
                </h5>
                <ul className="list-disc list-inside text-sm text-orange-600 space-y-1">
                  {explanation.potential_issues.map((issue, index) => (
                    <li key={index}>{issue}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const FileTreeNode = ({
  node,
  path,
  expandedFolders,
  onToggleFolder,
  onSelectFile,
  selectedFile,
}) => {
  const isExpanded = expandedFolders.has(path);
  const isSelected = selectedFile?.path === node.path;

  if (node.type === "file") {
    return (
      <div
        className={`flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-gray-100 ${
          isSelected ? "bg-blue-100 text-blue-700" : ""
        }`}
        onClick={() => onSelectFile(node)}
      >
        <File size={16} className="text-gray-400" />
        <span className="text-sm truncate">{node.name}</span>
        <span className="text-xs text-gray-400 ml-auto">{node.language}</span>
      </div>
    );
  }

  return (
    <div>
      <div
        className="flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-gray-100"
        onClick={() => onToggleFolder(path)}
      >
        {isExpanded ? (
          <ChevronDown size={16} className="text-gray-400" />
        ) : (
          <ChevronRight size={16} className="text-gray-400" />
        )}
        <Folder size={16} className="text-blue-500" />
        <span className="text-sm font-medium">{node.name}</span>
        {node.children && (
          <span className="text-xs text-gray-400 ml-auto">
            {Object.keys(node.children).length}
          </span>
        )}
      </div>
      {isExpanded && node.children && (
        <div className="ml-4 border-l border-gray-200 pl-2">
          {Object.entries(node.children).map(([name, child]) => (
            <FileTreeNode
              key={name}
              node={child}
              path={`${path}/${name}`}
              expandedFolders={expandedFolders}
              onToggleFolder={onToggleFolder}
              onSelectFile={onSelectFile}
              selectedFile={selectedFile}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const buildFileTree = (files) => {
  const tree = { type: "folder", name: "root", children: {} };

  files.forEach((file) => {
    const parts = file.path.split("/");
    let current = tree;

    parts.forEach((part, index) => {
      if (index === parts.length - 1) {
        current.children[part] = {
          type: "file",
          name: part,
          path: file.path,
          content: file.content,
          language: file.language,
          size: file.size,
        };
      } else {
        if (!current.children[part]) {
          current.children[part] = {
            type: "folder",
            name: part,
            children: {},
          };
        }
        current = current.children[part];
      }
    });
  });

  return tree;
};

export default CodeExplorer;
