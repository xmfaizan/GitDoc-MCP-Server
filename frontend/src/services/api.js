import axios from "axios";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use(
  (config) => {
    console.log(
      `Making ${config.method?.toUpperCase()} request to ${config.url}`
    );
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error("API Error:", error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const apiService = {
  async analyzeRepository(repoData) {
    try {
      const response = await api.post("/analyze-repo", repoData);
      return response.data;
    } catch (error) {
      throw new Error(
        error.response?.data?.detail || "Failed to analyze repository"
      );
    }
  },

  async explainCode(codeData) {
    try {
      const response = await api.post("/explain-code", codeData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || "Failed to explain code");
    }
  },

  async searchCode(searchData) {
    try {
      const response = await api.post("/search-code", searchData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || "Failed to search code");
    }
  },

  async getQualityMetrics(repoName) {
    try {
      const response = await api.get(
        `/quality-metrics/${encodeURIComponent(repoName)}`
      );
      return response.data;
    } catch (error) {
      throw new Error(
        error.response?.data?.detail || "Failed to get quality metrics"
      );
    }
  },

  async getSupportedLanguages() {
    try {
      const response = await api.get("/supported-languages");
      return response.data;
    } catch (error) {
      throw new Error(
        error.response?.data?.detail || "Failed to get supported languages"
      );
    }
  },

  async clearCache(repoName) {
    try {
      const response = await api.delete(
        `/cache/${encodeURIComponent(repoName)}`
      );
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || "Failed to clear cache");
    }
  },

  async healthCheck() {
    try {
      const response = await api.get("/health");
      return response.data;
    } catch (error) {
      throw new Error("Backend health check failed");
    }
  },
};

export const formatError = (error) => {
  if (error.response?.status === 422) {
    return "Invalid input data. Please check your repository URL.";
  } else if (error.response?.status === 404) {
    return "Repository not found. Please check the URL and try again.";
  } else if (error.response?.status === 500) {
    return "Server error. Please try again later.";
  } else if (error.code === "NETWORK_ERROR") {
    return "Network error. Please check your connection and ensure the backend is running.";
  }
  return error.message || "An unexpected error occurred";
};

export const validateGitHubUrl = (url) => {
  const githubPatterns = [
    /^https:\/\/github\.com\/[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+\/?$/,
    /^git@github\.com:[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+\.git$/,
    /^https:\/\/github\.com\/[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+\.git$/,
  ];

  return githubPatterns.some((pattern) => pattern.test(url.trim()));
};

export const extractRepoInfo = (url) => {
  const match = url.match(/github\.com\/([^\/]+)\/([^\/\.]+)/);
  if (match) {
    return {
      owner: match[1],
      repo: match[2],
    };
  }
  return null;
};

export default api;
