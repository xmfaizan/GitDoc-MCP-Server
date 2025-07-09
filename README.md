
# 🚀 GitHub Repo/Doc MCP Server

> AI-powered tool that analyzes GitHub repositories and generates comprehensive documentation automatically

## 📸 App Preview

![App](app-ui.png)


## 🎯 What It Does

1. **Enter any GitHub repository URL**
2. **AI analyzes the code** - quality, complexity, structure
3. **Generates beautiful documentation** - README, API docs, architecture guides
4. **Interactive code explorer** - browse code with AI explanations
5. **Quality metrics dashboard** - get actionable insights

## ✨ Key Features

- 🤖 **AI Code Analysis** - OpenAI GPT-3.5 powered insights
- 📊 **Quality Metrics** - Complexity, documentation coverage, maintainability scores
- 🔍 **Semantic Search** - Find code by meaning, not just keywords
- 📝 **Auto Documentation** - Generate README, API docs, architecture overviews
- 💻 **Interactive Explorer** - VS Code-like editor with AI explanations
- 🎯 **Multi-Language** - Python, JavaScript, Java, C++, Go, Rust, and more

## 🛠️ Tech Stack

### Backend
- **FastAPI** - High-performance Python API
- **OpenAI GPT-3.5** - AI code analysis
- **ChromaDB** - Vector database for semantic search
- **GitHub API** - Repository data fetching

### Frontend  
- **React 18** - Modern UI framework
- **Monaco Editor** - VS Code editor experience
- **Modern CSS** - Clean, responsive design

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 16+
- OpenAI API key
- GitHub Personal Access Token

### 1. Clone & Setup Backend
```bash
git clone <your-repo-url>
cd smart-code-docs/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add your API keys to .env file
```

### 2. Setup Frontend
```bash
cd ../frontend
npm install
```

### 3. Run the Application
```bash
# Terminal 1: Start backend
cd backend
uvicorn app.main:app --reload

# Terminal 2: Start frontend  
cd frontend
npm start
```

### 4. Open & Test
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Try analyzing: `https://github.com/pallets/flask`

## 📋 Environment Setup

Create `backend/.env` with your API keys:
```env
OPENAI_API_KEY=sk-your-openai-key-here
GITHUB_TOKEN=ghp-your-github-token-here
CHROMA_DB_PATH=./chroma_db
```

## 🎮 How to Use

1. **Start both servers** (backend on :8000, frontend on :3000)
2. **Enter GitHub repository URL** in the input field
3. **Click "Analyze Repository"** and wait for processing
4. **Explore results** in 4 tabs:
   - **Overview** - Documentation + quality metrics
   - **Code Explorer** - Interactive file browser with AI explanations
   - **Documentation** - Generated docs (README, API, architecture)
   - **Quality Score** - Detailed metrics and recommendations

## 🏗️ Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   React     │────│   FastAPI    │────│   OpenAI    │
│  Frontend   │    │   Backend    │    │   GPT-3.5   │
└─────────────┘    └──────────────┘    └─────────────┘
                           │
                   ┌───────┴───────┐
                   │               │
              ┌────────┐    ┌─────────────┐
              │GitHub  │    │  ChromaDB   │
              │  API   │    │(Vector DB)  │
              └────────┘    └─────────────┘
```

## 🎯 Demo Highlights

### AI-Powered Analysis
- **Code Quality Scoring** - Automated complexity and maintainability analysis
- **Smart Suggestions** - Language-specific improvement recommendations
- **Architecture Insights** - Repository-level structural analysis

### Interactive Features
- **Code Search** - "Find authentication functions" (semantic, not keyword)
- **AI Explanations** - Select any code block for detailed explanations  
- **Documentation Export** - Download generated docs as Markdown

### Quality Dashboard
- **Complexity Score** - Mathematical analysis of code complexity
- **Documentation Coverage** - Comment and docstring analysis
- **Maintainability Index** - Combined quality metrics
- **Language Breakdown** - Per-language quality statistics


## 🚧 Advanced Features

- **MCP Integration** - Model Context Protocol for advanced AI coordination
- **Vector Search** - Semantic code similarity matching
- **Multi-Architecture** - Both direct API and MCP-coordinated analysis
- **Caching System** - Fast repeated analysis of same repositories

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
