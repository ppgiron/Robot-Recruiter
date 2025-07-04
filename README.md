# Robot Recruiter

**Robot Recruiter** is an AI-powered, open-source platform designed to automate and streamline the technical recruiting process. It leverages GitHub data, AI models, and workflow automation to help organizations identify, assess, and manage software engineering talent more efficiently.

---

## 🚀 Project Overview

### What is Robot Recruiter?
Robot Recruiter is a modern recruiting assistant that automates the tedious parts of technical hiring, empowers human reviewers, and provides actionable insights—making the process faster, fairer, and more data-driven.

### Current Functionality (MVP)
- **Candidate Discovery:**
  - Scrapes and analyzes GitHub repositories and contributors to build a database of potential candidates.
  - Stores candidate profiles, including contributions, skills, and activity.
- **Feedback & Review Workflow:**
  - Allows recruiters and reviewers to assign, review, and provide feedback on candidate profiles.
  - Supports assignment of feedback to reviewers, tracking of review status, and review session management.
  - Reviewers can submit decisions (approved, rejected, needs revision) and notes.
- **Database & API:**
  - Uses SQLAlchemy ORM with support for both SQLite (for development/testing) and PostgreSQL (for production/integration).
  - Provides a REST API for candidate, feedback, and review session management.
- **Voice Notes (Experimental):**
  - Allows uploading and transcribing voice notes as part of the review process (early-stage feature).
- **Test Infrastructure:**
  - Robust unit and integration tests for core database and workflow logic.
  - Hybrid test setup for both SQLite and PostgreSQL.
- **CLI & Minimal UI:**
  - Command-line tools for managing candidates, feedback, and reviews.
  - A modern React-based web UI for interacting with the system.

### Future Functionality & Vision
- **AI-Powered Candidate Ranking:**
  - Use LLMs (e.g., GPT) to automatically assess and rank candidates based on code, contributions, and feedback.
- **Automated Interview Scheduling & Communication:**
  - Integrate with calendar/email systems to automate interview scheduling and candidate communication.
- **Advanced Analytics & Insights:**
  - Provide dashboards and analytics on recruiting pipeline, reviewer performance, and candidate quality.
- **Customizable Workflows:**
  - Support for custom review workflows, multi-stage interviews, and role-specific assessments.
- **Integration with External Platforms:**
  - Connect with LinkedIn, job boards, and HR systems for a unified recruiting pipeline.
- **Enhanced Voice/Video Feedback:**
  - Improved support for voice and video notes, including AI-powered transcription and sentiment analysis.
- **Security & Compliance:**
  - Role-based access control, audit logs, and compliance features for enterprise use.

---

# Robot Recruiter UI

A modern React-based user interface for the Robot Recruiter platform - an AI-powered system for analyzing, classifying, and recruiting engineering talent from GitHub repositories.

## 🚀 Features

- **Modern React 18** with TypeScript for type safety
- **Vite** for fast development and building
- **Tailwind CSS** for utility-first styling
- **React Router** for client-side routing
- **React Query** for server state management
- **Lucide React** for beautiful icons
- **Framer Motion** for smooth animations
- **Responsive Design** that works on all devices

## 📋 Prerequisites

- Node.js 18+ 
- npm or yarn
- Robot Recruiter backend API running on `http://localhost:8000`

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd robot-recruiter-ui
   ```

2. **Install dependencies**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Start the development server**
   ```bash
   npm run dev
   # or
   yarn dev
   ```

4. **Open your browser**
   Navigate to `http://localhost:3000`

## 🏗️ Project Structure

```
src/
├── components/          # Reusable UI components
│   └── Layout.tsx      # Main layout with navigation
├── pages/              # Page components
│   ├── Dashboard.tsx   # Main dashboard
│   ├── RepositoryAnalysis.tsx
│   ├── Candidates.tsx
│   ├── CandidateDetail.tsx
│   ├── Settings.tsx
│   └── NotFound.tsx
├── hooks/              # Custom React hooks
├── lib/                # Utility libraries
├── types/              # TypeScript type definitions
├── utils/              # Helper functions
├── App.tsx             # Main app component
├── main.tsx            # Application entry point
└── index.css           # Global styles
```

## 🎨 Design System

The UI uses a comprehensive design system with:

- **Color Palette**: Primary blue, secondary grays, and semantic colors
- **Typography**: Inter font family for clean readability
- **Components**: Pre-built buttons, cards, inputs, and badges
- **Spacing**: Consistent spacing scale
- **Animations**: Smooth transitions and micro-interactions

### Color Scheme

- **Primary**: Blue (#3B82F6) for main actions and branding
- **Secondary**: Gray scale for text and backgrounds
- **Success**: Green for positive states
- **Warning**: Orange for caution states
- **Danger**: Red for error states

## 📱 Pages

### Dashboard
- Overview statistics and metrics
- Recent activity feed
- Quick action buttons
- System status indicators

### Repository Analysis
- Form to input repository URLs
- Analysis configuration options
- Real-time progress tracking
- Results visualization

### Candidates
- Search and filter candidates
- Grid/list view options
- Advanced filtering by skills, location, company
- Export functionality

### Candidate Detail
- Comprehensive profile view
- Contribution history
- Skills and expertise breakdown
- Contact information

### Settings
- API configuration
- User preferences
- System settings
- Integration options

## 🔧 Development

### Available Scripts

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linting
npm run lint

# Run tests
npm run test

# Run tests with UI
npm run test:ui
```

### Code Style

The project uses:
- **ESLint** for code linting
- **Prettier** for code formatting
- **TypeScript** for type checking
- **Tailwind CSS** for styling

### API Integration

The UI communicates with the Robot Recruiter backend API:

- **Base URL**: `http://localhost:8000`
- **Proxy**: Configured in Vite for development
- **Authentication**: GitHub OAuth integration
- **Data Fetching**: React Query for caching and state management

## 🧪 Testing

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage

# Run tests with UI
npm run test:ui
```

## 📦 Building for Production

```bash
# Build the application
npm run build

# Preview the production build
npm run preview
```

The build output will be in the `dist/` directory.

## 🌐 Deployment

### Vercel (Recommended)

1. Connect your repository to Vercel
2. Set environment variables:
   - `VITE_API_URL`: Your backend API URL
3. Deploy automatically on push to main branch

### Netlify

1. Connect your repository to Netlify
2. Set build command: `npm run build`
3. Set publish directory: `dist`
4. Configure environment variables

### Docker

```dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npm", "run", "preview"]
```

## 🔒 Environment Variables

Create a `.env` file in the root directory:

```env
# API Configuration
VITE_API_URL=http://localhost:8000

# GitHub OAuth
VITE_GITHUB_CLIENT_ID=your_github_client_id

# Feature Flags
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_FEEDBACK=true
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Guidelines

- Follow TypeScript best practices
- Write meaningful commit messages
- Add tests for new features
- Update documentation as needed
- Follow the existing code style

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the [docs](./docs) directory
- **Issues**: Report bugs and feature requests on GitHub
- **Discussions**: Join the community discussions

## 🔗 Related Projects

- [Robot Recruiter UI](https://github.com/ppgiron/robot-recruiter-ui) - React Web Interface

---

Built with ❤️ by the Robot Recruiter team 