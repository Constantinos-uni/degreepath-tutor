# DegreePath Tutor - Frontend

React-based web interface for the DegreePath Tutor application.

## Technology Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first styling
- **Shadcn/UI** - Component library
- **Lucide React** - Icon library

## Prerequisites

- Node.js 18+ or Bun
- npm, yarn, or bun package manager

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Configure environment (optional):
   ```bash
   cp .env.example .env
   # Edit .env if using non-default API URLs
   ```

3. Start development server:
   ```bash
   npm run dev
   ```

4. Open http://localhost:5173 in your browser

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_PART1_API_URL` | `http://localhost:8000` | Part 1 API (Eligibility Engine) |
| `VITE_PART2_API_URL` | `http://localhost:8001` | Part 2 API (AI Tutor) |

## Project Structure

```
src/
├── components/     # Reusable UI components
│   └── ui/         # Shadcn/UI components
├── hooks/          # Custom React hooks
├── lib/            # Utilities and API client
├── pages/          # Page components
│   ├── Dashboard.tsx
│   ├── Chat.tsx
│   ├── Eligibility.tsx
│   ├── Students.tsx
│   └── UnitSearch.tsx
└── App.tsx         # Main application entry
```

## Build for Production

```bash
npm run build
```

Output will be in the `dist/` directory.

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |
