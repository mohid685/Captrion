# Captrion Frontend Setup

## Overview
This document describes the frontend setup for the Captrion financial advisor application. The frontend is a modern, dark-themed React application built with Vite, TypeScript, and Chakra UI.

## Features
- Dark aesthetic theme
- User authentication (login/register)
- Dashboard with portfolio statistics
- Agentic AI chat interface for stock advice
- Portfolio management view
- Responsive design

## Technology Stack
- React 18
- TypeScript
- Vite (build tool)
- Chakra UI (component library)
- React Router (client-side routing)
- Fetch API (for backend communication)

## Project Structure
```
frontend/
├── public/                 # Static assets
├── src/
│   ├── components/         # Reusable components (Header, Footer)
│   ├── context/            # React contexts (AuthContext)
│   ├── pages/              # Page components
│   │   ├── ChatPage.tsx    # AI chat interface
│   │   ├── DashboardPage.tsx # Portfolio dashboard
│   │   ├── HomePage.tsx    # Landing page
│   │   ├── LoginPage.tsx   # User login
│   │   ├── PortfolioPage.tsx # Portfolio holdings
│   │   └── RegisterPage.tsx # User registration
│   ├── App.tsx             # Main app component with routing
│   ├── main.tsx            # Entry point
│   └── index.css           # Global styles
├── package.json            # Dependencies and scripts
├── tsconfig.json           # TypeScript configuration
└── vite.config.ts          # Vite configuration
```

## Setup Instructions

### Prerequisites
- Node.js (v18 or higher)
- npm (comes with Node.js)
- Backend server running on `http://localhost:8000`

### Installation
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies (if not already installed):
   ```bash
   npm install
   ```

### Development Server
To start the frontend in development mode:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`.

### Production Build
To create a production build:
```bash
npm run build
```

The built assets will be in the `dist/` directory.

To preview the production build:
```bash
npm run preview
```

## Backend Integration
The frontend communicates with the backend API running on `http://localhost:8000`. Make sure the backend is running before starting the frontend.

Key API endpoints used:
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `GET /dashboard/stats` - Dashboard statistics (requires auth)
- `GET /portfolio/` - User portfolio holdings (requires auth)
- `POST /advisor/{ticker}/ask-agentic` - Agentic AI advice (requires auth)
- `GET /conversations/{userId}` - Chat history (requires auth)

## Environment Variables
The frontend uses the following default backend URL:
- `http://localhost:8000`

To change the backend URL, modify the fetch requests in the components or create a `.env` file in the frontend directory with:
```
VITE_API_URL=http://your-backend-url:port
```

Then use `import.meta.env.VITE_API_URL` in your code.

## Design Notes
- Dark theme is enforced as the default color mode
- Chakra UI provides accessible, responsive components
- All pages are protected by authentication (except login/register)
- Loading states and error handling are implemented
- Toast notifications provide user feedback

## Troubleshooting
1. **Cannot connect to backend**: Ensure the backend is running on `http://localhost:8000` and there are no network issues.
2. **Authentication issues**: Check that the backend auth endpoints are working correctly.
3. **Build errors**: Make sure all dependencies are installed and TypeScript compiles without errors.

## Further Enhancements
- Add real-time updates with WebSocket
- Implement refresh token flow
- Add more sophisticated charts and visualizations
- Implement portfolio editing capabilities
- Add dark/light mode toggle