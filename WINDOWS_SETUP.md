# Robot Recruiter - Windows Setup Guide

This guide will help you set up the Robot Recruiter project on Windows and enable collaboration with other developers.

## 🖥️ System Requirements

- **Windows 10/11** (64-bit)
- **8GB RAM** minimum (16GB recommended)
- **10GB free disk space**
- **Git** for version control
- **Python 3.9+** for backend
- **Node.js 18+** for frontend

## 📋 Prerequisites Installation

### 1. Install Git
1. Download Git for Windows from: https://git-scm.com/download/win
2. Run the installer with default settings
3. Verify installation: `git --version`

### 2. Install Python
1. Download Python 3.11+ from: https://www.python.org/downloads/
2. **Important**: Check "Add Python to PATH" during installation
3. Verify installation: `python --version`

### 3. Install Node.js
1. Download Node.js 18+ from: https://nodejs.org/
2. Run the installer with default settings
3. Verify installation: `node --version` and `npm --version`

### 4. Install Visual Studio Code (Recommended)
1. Download VS Code from: https://code.visualstudio.com/
2. Install with default settings
3. Install recommended extensions:
   - Python
   - TypeScript and JavaScript Language Features
   - GitLens
   - Tailwind CSS IntelliSense

## 🚀 Project Setup

### 1. Clone the Repository
```bash
# Open Command Prompt or PowerShell
git clone <your-repository-url>
cd Robot-Recruiter
```

### 2. Backend Setup (Python)

#### Create Virtual Environment
```bash
# In the Robot-Recruiter directory
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# You should see (venv) in your prompt
```

#### Install Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -e ".[dev]"
```

#### Environment Configuration
```bash
# Copy environment template
copy env.template .env

# Edit .env file with your configuration
notepad .env
```

Required environment variables:
```env
# GitHub OAuth (required for API access)
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# Database (SQLite for development)
DATABASE_URL=sqlite:///robot_recruiter.db

# OpenAI (optional, for AI features)
OPENAI_API_KEY=your_openai_api_key
```

### 3. Frontend Setup (React/TypeScript)

#### Navigate to UI Directory
```bash
cd robot-recruiter-ui
```

#### Install Dependencies
```bash
npm install
```

#### Environment Configuration
```bash
# Create .env file for frontend
echo VITE_API_URL=http://localhost:8000 > .env
```

## 🏃‍♂️ Running the Application

### Start Backend Server
```bash
# In Robot-Recruiter directory with venv activated
python -m src.github_talent_intelligence.api
```

The backend will start on `http://localhost:8000`

### Start Frontend Development Server
```bash
# In robot-recruiter-ui directory
npm run dev
```

The frontend will start on `http://localhost:3000`

## 🔧 Development Workflow

### Backend Development
```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=src

# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
flake8 src/ tests/
```

### Frontend Development
```bash
# Run tests
npm test

# Run tests with UI
npm run test:ui

# Lint code
npm run lint

# Build for production
npm run build
```

## 🤝 Collaboration Setup

### 1. Git Workflow
```bash
# Create a new branch for your feature
git checkout -b feature/your-feature-name

# Make your changes
# ... edit files ...

# Stage and commit changes
git add .
git commit -m "Add feature description"

# Push to remote
git push origin feature/your-feature-name

# Create Pull Request on GitHub
```

### 2. Code Style Guidelines
- **Python**: Use Black for formatting, isort for imports
- **TypeScript**: Use ESLint and Prettier
- **Commit Messages**: Use conventional commits format

### 3. Database Setup for Collaboration
```bash
# Initialize database (first time only)
python -m src.github_talent_intelligence.db init

# Run migrations (if any)
python -m src.github_talent_intelligence.db migrate
```

## 🐛 Troubleshooting

### Common Issues

#### Python Path Issues
```bash
# If python command not found
py --version
# Use py instead of python on Windows
```

#### Virtual Environment Issues
```bash
# If venv activation fails
venv\Scripts\activate.bat
# Or use PowerShell
venv\Scripts\Activate.ps1
```

#### Node.js Issues
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rmdir /s node_modules
npm install
```

#### Port Conflicts
```bash
# Check what's using port 8000
netstat -ano | findstr :8000

# Check what's using port 3000
netstat -ano | findstr :3000
```

### Performance Optimization

#### For Large Repositories
```bash
# Increase Git buffer size
git config --global http.postBuffer 524288000

# Use Git LFS for large files
git lfs install
```

#### For Development
```bash
# Enable Windows Developer Mode
# Settings > Update & Security > For developers > Developer Mode

# Use WSL2 for better performance (optional)
# Install WSL2 from Microsoft Store
```

## 📚 Additional Resources

- [Python on Windows](https://docs.python.org/3/using/windows.html)
- [Node.js on Windows](https://nodejs.org/en/docs/guides/nodejs-docker-webapp/)
- [Git for Windows](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [VS Code Setup](https://code.visualstudio.com/docs/setup/setup-overview)

## 🆘 Getting Help

1. Check the troubleshooting section above
2. Review the project documentation in `/docs`
3. Check GitHub Issues for known problems
4. Ask in the project's discussion forum
5. Contact the maintainers

## ✅ Verification Checklist

- [ ] Git installed and configured
- [ ] Python 3.9+ installed and in PATH
- [ ] Node.js 18+ installed
- [ ] Virtual environment created and activated
- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed
- [ ] Environment variables configured
- [ ] Backend server starts successfully
- [ ] Frontend development server starts successfully
- [ ] Can access http://localhost:3000
- [ ] Can access http://localhost:8000
- [ ] Tests pass for both backend and frontend 