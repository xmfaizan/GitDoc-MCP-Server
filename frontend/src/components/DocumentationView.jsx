import React, { useState } from "react";
import {
  FileText,
  Download,
  Copy,
  Check,
  Book,
  Settings,
  Layers,
  Code2,
  ExternalLink,
} from "lucide-react";

const DocumentationView = ({ documentation, repoInfo }) => {
  const [activeTab, setActiveTab] = useState("overview");
  const [copiedSection, setCopiedSection] = useState(null);

  const copyToClipboard = async (text, section) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedSection(section);
      setTimeout(() => setCopiedSection(null), 2000);
    } catch (err) {
      console.error("Failed to copy text: ", err);
    }
  };

  const downloadDocumentation = () => {
    const fullDoc = `# ${documentation.repo_name} Documentation

${documentation.overview}

${documentation.installation_guide}

## Usage Examples
${documentation.usage_examples.join("\n\n")}

${documentation.architecture_overview}

## API Documentation
${documentation.api_documentation
  .map(
    (section) => `
### ${section.title}
${section.content}
${section.code_examples.join("\n\n")}
`
  )
  .join("\n")}

---
Generated on ${new Date(documentation.generated_at).toLocaleString()}
Quality Score: ${documentation.quality_score}/10
`;

    const blob = new Blob([fullDoc], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${documentation.repo_name}-documentation.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const tabs = [
    { id: "overview", label: "Overview", icon: Book },
    { id: "installation", label: "Installation", icon: Settings },
    { id: "usage", label: "Usage", icon: Code2 },
    { id: "api", label: "API Docs", icon: FileText },
    { id: "architecture", label: "Architecture", icon: Layers },
  ];

  const renderMarkdown = (text) => {
    return text
      .replace(
        /^# (.*$)/gim,
        '<h1 class="text-3xl font-bold text-gray-800 mb-4">$1</h1>'
      )
      .replace(
        /^## (.*$)/gim,
        '<h2 class="text-2xl font-bold text-gray-700 mb-3 mt-6">$2</h2>'
      )
      .replace(
        /^### (.*$)/gim,
        '<h3 class="text-xl font-semibold text-gray-600 mb-2 mt-4">$3</h3>'
      )
      .replace(/\*\*(.*?)\*\*/gim, '<strong class="font-semibold">$1</strong>')
      .replace(/\*(.*?)\*/gim, '<em class="italic">$1</em>')
      .replace(
        /`(.*?)`/gim,
        '<code class="bg-gray-100 px-2 py-1 rounded text-sm font-mono">$1</code>'
      )
      .replace(
        /```([\s\S]*?)```/gim,
        '<pre class="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto my-4"><code>$1</code></pre>'
      )
      .replace(/^- (.*$)/gim, '<li class="ml-4">$1</li>')
      .replace(/\n/gim, "<br>");
  };

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden">
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-2">Documentation</h2>
            <div className="flex items-center gap-4 text-blue-100">
              <span className="flex items-center gap-1">
                <FileText size={16} />
                {documentation.repo_name}
              </span>
              <span className="flex items-center gap-1">
                Quality Score: {documentation.quality_score}/10
              </span>
              <span className="text-xs">
                Generated{" "}
                {new Date(documentation.generated_at).toLocaleDateString()}
              </span>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={downloadDocumentation}
              className="flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors"
            >
              <Download size={16} />
              Download
            </button>
            {documentation.repo_url && (
              <a
                href={documentation.repo_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors"
              >
                <ExternalLink size={16} />
                Repository
              </a>
            )}
          </div>
        </div>
      </div>

      <div className="border-b border-gray-200">
        <div className="flex overflow-x-auto">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-6 py-4 whitespace-nowrap border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? "border-blue-500 text-blue-600 bg-blue-50"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50"
                }`}
              >
                <Icon size={18} />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="p-6">
        {activeTab === "overview" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-gray-800">
                Project Overview
              </h3>
              <button
                onClick={() =>
                  copyToClipboard(documentation.overview, "overview")
                }
                className="flex items-center gap-2 px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                {copiedSection === "overview" ? (
                  <Check size={16} />
                ) : (
                  <Copy size={16} />
                )}
                {copiedSection === "overview" ? "Copied!" : "Copy"}
              </button>
            </div>
            <div
              className="prose prose-blue max-w-none"
              dangerouslySetInnerHTML={{
                __html: renderMarkdown(documentation.overview),
              }}
            />
          </div>
        )}

        {activeTab === "installation" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-gray-800">
                Installation Guide
              </h3>
              <button
                onClick={() =>
                  copyToClipboard(
                    documentation.installation_guide,
                    "installation"
                  )
                }
                className="flex items-center gap-2 px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                {copiedSection === "installation" ? (
                  <Check size={16} />
                ) : (
                  <Copy size={16} />
                )}
                {copiedSection === "installation" ? "Copied!" : "Copy"}
              </button>
            </div>
            <div
              className="prose prose-blue max-w-none"
              dangerouslySetInnerHTML={{
                __html: renderMarkdown(documentation.installation_guide),
              }}
            />
          </div>
        )}

        {activeTab === "usage" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-gray-800">
                Usage Examples
              </h3>
              <button
                onClick={() =>
                  copyToClipboard(
                    documentation.usage_examples.join("\n\n"),
                    "usage"
                  )
                }
                className="flex items-center gap-2 px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                {copiedSection === "usage" ? (
                  <Check size={16} />
                ) : (
                  <Copy size={16} />
                )}
                {copiedSection === "usage" ? "Copied!" : "Copy"}
              </button>
            </div>
            {documentation.usage_examples.map((example, index) => (
              <div key={index} className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold text-gray-700">
                    Example {index + 1}
                  </h4>
                  <button
                    onClick={() => copyToClipboard(example, `usage-${index}`)}
                    className="text-sm text-gray-500 hover:text-gray-700"
                  >
                    {copiedSection === `usage-${index}` ? (
                      <Check size={14} />
                    ) : (
                      <Copy size={14} />
                    )}
                  </button>
                </div>
                <div
                  className="prose prose-sm max-w-none"
                  dangerouslySetInnerHTML={{
                    __html: renderMarkdown(example),
                  }}
                />
              </div>
            ))}
          </div>
        )}

        {activeTab === "api" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-gray-800">
                API Documentation
              </h3>
              <span className="text-sm text-gray-500">
                {documentation.api_documentation.length} sections
              </span>
            </div>
            {documentation.api_documentation.length > 0 ? (
              documentation.api_documentation.map((section, index) => (
                <div
                  key={index}
                  className="border border-gray-200 rounded-lg p-4"
                >
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-lg font-semibold text-gray-700">
                      {section.title}
                    </h4>
                    <button
                      onClick={() =>
                        copyToClipboard(section.content, `api-${index}`)
                      }
                      className="text-sm text-gray-500 hover:text-gray-700"
                    >
                      {copiedSection === `api-${index}` ? (
                        <Check size={14} />
                      ) : (
                        <Copy size={14} />
                      )}
                    </button>
                  </div>
                  <div
                    className="prose prose-sm max-w-none mb-4"
                    dangerouslySetInnerHTML={{
                      __html: renderMarkdown(section.content),
                    }}
                  />
                  {section.code_examples.length > 0 && (
                    <div className="space-y-2">
                      <h5 className="font-medium text-gray-600">
                        Code Examples:
                      </h5>
                      {section.code_examples.map((example, exampleIndex) => (
                        <div
                          key={exampleIndex}
                          className="prose prose-sm max-w-none"
                          dangerouslySetInnerHTML={{
                            __html: renderMarkdown(example),
                          }}
                        />
                      ))}
                    </div>
                  )}
                  {section.related_files.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-100">
                      <span className="text-sm text-gray-500">
                        Related files: {section.related_files.join(", ")}
                      </span>
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-gray-500">
                <FileText size={48} className="mx-auto mb-4 text-gray-300" />
                <p>No API documentation sections generated</p>
                <p className="text-sm">
                  This may be due to the repository structure or content type
                </p>
              </div>
            )}
          </div>
        )}

        {activeTab === "architecture" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-gray-800">
                Architecture Overview
              </h3>
              <button
                onClick={() =>
                  copyToClipboard(
                    documentation.architecture_overview,
                    "architecture"
                  )
                }
                className="flex items-center gap-2 px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                {copiedSection === "architecture" ? (
                  <Check size={16} />
                ) : (
                  <Copy size={16} />
                )}
                {copiedSection === "architecture" ? "Copied!" : "Copy"}
              </button>
            </div>
            <div
              className="prose prose-blue max-w-none"
              dangerouslySetInnerHTML={{
                __html: renderMarkdown(documentation.architecture_overview),
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentationView;
