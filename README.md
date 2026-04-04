# SmartShift+

Monolithic repository for **SmartShift+**, a platform protecting gig delivery workers against income loss.

## Tech Stack Overview

- **Mobile App**: React Native (Expo)
- **Backend API**: Python FastAPI
- **Web Dashboard**: React.js, TailwindCSS
- **ML Engine**: Python, Scikit-learn / Statsmodels prototypes

## Quick Start

1. Start the Docker containers:
```bash
docker-compose up -d
```
2. Setup Mobile App:
```bash
cd mobile
npm install
npm run start
```
3. Setup Dashboard:
```bash
cd dashboard
npm install
npm run dev
```
