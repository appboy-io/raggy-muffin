# Frontend UI

A modern React frontend for the AI Document Assistant platform.

## Features

- **Modern React 18** with hooks and functional components
- **Tailwind CSS** for styling and responsive design
- **React Query** for data fetching and caching
- **React Router** for navigation
- **React Dropzone** for file uploads
- **React Hot Toast** for notifications
- **Heroicons** for icons
- **Authentication** integration with JWT tokens
- **Real-time chat** interface
- **File upload** with progress tracking
- **Mobile responsive** design

## Development

### Prerequisites

- Node.js 18+
- npm or yarn

### Setup

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
cp .env.example .env.local
```

3. Start development server:
```bash
npm start
```

The app will be available at `http://localhost:3000`

### Docker Development

Run with Docker Compose:
```bash
docker-compose -f docker-compose.frontend-dev.yml up frontend-ui
```

## Building

### Production Build

```bash
npm run build
```

### Docker Production Build

```bash
docker build -t frontend-ui .
```

## Environment Variables

- `REACT_APP_API_URL` - API backend URL
- `REACT_APP_BRAND_NAME` - Application brand name
- `REACT_APP_BRAND_LOGO` - Brand logo emoji/text
- `REACT_APP_PRIMARY_COLOR` - Primary theme color
- `REACT_APP_SECONDARY_COLOR` - Secondary theme color
- `REACT_APP_WIDGET_DOMAIN` - Widget domain URL

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── ErrorBoundary.js
│   └── Layout.js
├── context/            # React contexts
│   ├── AuthContext.js
│   └── ConfigContext.js
├── pages/              # Page components
│   ├── Chat.js
│   ├── Home.js
│   ├── Login.js
│   ├── Register.js
│   └── Upload.js
├── services/           # API and external services
│   └── api.js
├── App.js              # Main app component
├── index.js            # Entry point
└── index.css           # Global styles
```

## Performance Optimizations

- **Code splitting** with React.lazy()
- **Image optimization** with next/image
- **Bundle analysis** with webpack-bundle-analyzer
- **Caching** with React Query
- **Lazy loading** for routes and components
- **Gzip compression** in production
- **Static asset serving** with serve package

## Deployment

The app is containerized and can be deployed using Docker:

```bash
# Build production image
docker build -t frontend-ui .

# Run container
docker run -p 80:80 frontend-ui
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

This project is proprietary software.