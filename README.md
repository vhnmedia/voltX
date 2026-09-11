# GreenWatt Static Prototype — Enhanced UI

A production-style GreenWatt product prototype built with plain HTML, CSS and JavaScript while using a componentized SPA architecture similar to a React application.

## What is included

- Public marketing pages and enterprise login/onboarding
- Responsive authenticated application with grouped sidebar navigation
- Enhanced post-login Overview dashboard and market context
- Workspace search / command palette (`Ctrl/Cmd + K`)
- DAM market price forecasting with 96-block demo data
- Weather, renewable and load forecast screens
- Procurement planner and linear-programming optimizer interface
- Live-market and simulated execution workflows
- Trade history, CSV export and printable/PDF reports
- KYC, eligibility, company profile and settings screens
- Coherent fixed demo data for ABC Manufacturing Pvt. Ltd.

## Run locally

Use any static server (recommended because the app uses browser APIs and hash routing):

```bash
python3 -m http.server 8080
```

Then open `http://localhost:8080`.

## Demo login

- Email: `demo@greenwatt.in`
- Password: any 6+ characters (for example `demo123`)

You can also click **View Demo** from the landing page.

## Deploy to Vercel

This repository is a static site. The included `vercel.json` sends all routes to `index.html`; hash routes work without additional configuration.

## Important demo note

Authentication, KYC verification and electricity-market execution are frontend simulations in this static prototype. The UI clearly labels simulated market activity and should be connected to the FastAPI/PostgreSQL backend before production use.
