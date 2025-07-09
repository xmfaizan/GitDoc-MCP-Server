import React, { useState, useEffect } from "react";
import {
  Award,
  TrendingUp,
  FileText,
  Zap,
  Shield,
  Target,
  AlertTriangle,
  CheckCircle,
  Info,
} from "lucide-react";

const QualityScore = ({ analysisData, documentation }) => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const calculateMetrics = () => {
      setLoading(true);

      const analysis = analysisData?.analysis || [];
      const files = analysisData?.files || [];

      // Calculate documentation coverage
      const docScores = analysis.map((a) => a.documentation_quality || 0);
      const docCoverage =
        docScores.length > 0
          ? docScores.reduce((a, b) => a + b, 0) / docScores.length
          : 0;

      // Calculate complexity
      const complexityScores = analysis.map((a) => a.complexity_score || 0);
      const avgComplexity =
        complexityScores.length > 0
          ? complexityScores.reduce((a, b) => a + b, 0) /
            complexityScores.length
          : 0;

      // Calculate maintainability (inverse of complexity + documentation)
      const maintainability = (docCoverage + (10 - avgComplexity)) / 2;

      // Estimate test coverage
      const testFiles = analysis.filter((a) =>
        a.file_path.toLowerCase().includes("test")
      ).length;
      const testCoverage =
        files.length > 0 ? Math.min((testFiles / files.length) * 100, 100) : 0;

      // Overall score
      const overallScore =
        documentation?.quality_score ||
        docCoverage * 0.3 +
          (10 - avgComplexity) * 0.3 +
          maintainability * 0.2 +
          (testCoverage / 10) * 0.2;

      // Generate recommendations
      const recommendations = [];
      if (docCoverage < 5)
        recommendations.push({
          type: "warning",
          text: "Improve code documentation and comments",
        });
      if (avgComplexity > 7)
        recommendations.push({
          type: "warning",
          text: "Reduce code complexity by refactoring large functions",
        });
      if (testCoverage < 30)
        recommendations.push({
          type: "info",
          text: "Add more unit tests for better coverage",
        });
      if (overallScore >= 8)
        recommendations.push({
          type: "success",
          text: "Excellent code quality! Keep up the good work",
        });
      else if (overallScore >= 6)
        recommendations.push({
          type: "info",
          text: "Good code quality with room for improvement",
        });
      else
        recommendations.push({
          type: "warning",
          text: "Consider focusing on code quality improvements",
        });

      // Additional insights
      const languageStats = {};
      analysis.forEach((a) => {
        if (!languageStats[a.language]) {
          languageStats[a.language] = { count: 0, avgComplexity: 0, avgDoc: 0 };
        }
        languageStats[a.language].count++;
        languageStats[a.language].avgComplexity += a.complexity_score || 0;
        languageStats[a.language].avgDoc += a.documentation_quality || 0;
      });

      Object.keys(languageStats).forEach((lang) => {
        const stats = languageStats[lang];
        stats.avgComplexity /= stats.count;
        stats.avgDoc /= stats.count;
      });

      setMetrics({
        documentation_coverage: Math.round(docCoverage * 10) / 10,
        code_complexity: Math.round(avgComplexity * 10) / 10,
        maintainability_score: Math.round(maintainability * 10) / 10,
        test_coverage: Math.round(testCoverage * 10) / 10,
        overall_score: Math.round(overallScore * 10) / 10,
        recommendations,
        languageStats,
        totalFiles: files.length,
        analyzedFiles: analysis.length,
      });

      setLoading(false);
    };

    if (analysisData && documentation) {
      calculateMetrics();
    }
  }, [analysisData, documentation]);

  const getScoreColor = (score, reverse = false) => {
    if (reverse) score = 10 - score;
    if (score >= 8) return "text-green-600";
    if (score >= 6) return "text-yellow-600";
    return "text-red-600";
  };

  const getScoreBgColor = (score, reverse = false) => {
    if (reverse) score = 10 - score;
    if (score >= 8) return "bg-green-500";
    if (score >= 6) return "bg-yellow-500";
    return "bg-red-500";
  };

  const CircularProgress = ({
    value,
    max = 10,
    size = 120,
    strokeWidth = 8,
    color = "#3B82F6",
  }) => {
    const radius = (size - strokeWidth) / 2;
    const circumference = radius * 2 * Math.PI;
    const offset = circumference - (value / max) * circumference;

    return (
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="#E5E7EB"
            strokeWidth={strokeWidth}
            fill="none"
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={color}
            strokeWidth={strokeWidth}
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-800">
              {value.toFixed(1)}
            </div>
            <div className="text-xs text-gray-500">/ {max}</div>
          </div>
        </div>
      </div>
    );
  };

  const MetricCard = ({
    title,
    value,
    max = 10,
    icon: Icon,
    color,
    reverse = false,
  }) => (
    <div className="bg-white rounded-lg p-6 shadow-md border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div
            className={`p-2 rounded-lg ${
              color === "green"
                ? "bg-green-100"
                : color === "blue"
                ? "bg-blue-100"
                : color === "purple"
                ? "bg-purple-100"
                : "bg-orange-100"
            }`}
          >
            <Icon
              size={20}
              className={`${
                color === "green"
                  ? "text-green-600"
                  : color === "blue"
                  ? "text-blue-600"
                  : color === "purple"
                  ? "text-purple-600"
                  : "text-orange-600"
              }`}
            />
          </div>
          <h3 className="font-semibold text-gray-700">{title}</h3>
        </div>
        <span className={`text-2xl font-bold ${getScoreColor(value, reverse)}`}>
          {value.toFixed(1)}
        </span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-3">
        <div
          className={`h-3 rounded-full transition-all duration-1000 ease-out ${getScoreBgColor(
            value,
            reverse
          )}`}
          style={{ width: `${(value / max) * 100}%` }}
        />
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-8">
        <div className="flex items-center gap-3 mb-6">
          <Award className="text-blue-600" size={28} />
          <h2 className="text-2xl font-bold text-gray-800">Quality Metrics</h2>
        </div>
        <div className="flex items-center justify-center py-12">
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-8">
        <div className="flex items-center gap-3 mb-6">
          <Award className="text-blue-600" size={28} />
          <h2 className="text-2xl font-bold text-gray-800">Quality Metrics</h2>
        </div>
        <div className="text-center py-12 text-gray-500">
          <Award size={48} className="mx-auto mb-4 text-gray-300" />
          <p>No metrics available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden">
      <div className="gradient-blue-purple text-white p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Award size={28} />
            <div>
              <h2 className="text-2xl font-bold">Quality Metrics</h2>
              <p className="text-blue-100">
                {metrics.analyzedFiles} of {metrics.totalFiles} files analyzed
              </p>
            </div>
          </div>
          <div className="text-center">
            <CircularProgress
              value={metrics.overall_score}
              max={10}
              size={100}
              color="#FFFFFF"
            />
          </div>
        </div>
      </div>

      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <MetricCard
            title="Documentation"
            value={metrics.documentation_coverage}
            icon={FileText}
            color="blue"
          />
          <MetricCard
            title="Complexity"
            value={metrics.code_complexity}
            icon={Zap}
            color="orange"
            reverse={true}
          />
          <MetricCard
            title="Maintainability"
            value={metrics.maintainability_score}
            icon={Shield}
            color="green"
          />
          <MetricCard
            title="Test Coverage"
            value={metrics.test_coverage}
            max={100}
            icon={Target}
            color="purple"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <TrendingUp size={20} />
              Recommendations
            </h3>
            <div className="space-y-3">
              {metrics.recommendations.map((rec, index) => {
                const IconComponent =
                  rec.type === "success"
                    ? CheckCircle
                    : rec.type === "warning"
                    ? AlertTriangle
                    : Info;
                const colorClass =
                  rec.type === "success"
                    ? "text-green-600 bg-green-50"
                    : rec.type === "warning"
                    ? "text-orange-600 bg-orange-50"
                    : "text-blue-600 bg-blue-50";

                return (
                  <div
                    key={index}
                    className={`flex items-start gap-3 p-3 rounded-lg ${colorClass}`}
                  >
                    <IconComponent size={18} className="mt-0.5 flex-shrink-0" />
                    <span className="text-sm">{rec.text}</span>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
              Language Breakdown
            </h3>
            <div className="space-y-4">
              {Object.entries(metrics.languageStats).map(
                ([language, stats]) => (
                  <div key={language} className="bg-white rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-gray-700 capitalize">
                        {language}
                      </span>
                      <span className="text-sm text-gray-500">
                        {stats.count} files
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Complexity: </span>
                        <span
                          className={getScoreColor(stats.avgComplexity, true)}
                        >
                          {stats.avgComplexity.toFixed(1)}/10
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Documentation: </span>
                        <span className={getScoreColor(stats.avgDoc)}>
                          {stats.avgDoc.toFixed(1)}/10
                        </span>
                      </div>
                    </div>
                  </div>
                )
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QualityScore;
