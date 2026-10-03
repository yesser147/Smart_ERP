# Frontend (Angular 17)

The web application of Nexus ERP. It normally runs in Docker (see the main `README.md`).

For development without Docker (Node 18+):

```powershell
npm install
npm start          # http://localhost:4200, reloads on every change
npm run build      # production build in dist/
```

The two API addresses (backend and AI engine) are in `src/environments/`.

| Folder | Content |
|---|---|
| `src/app/core` | guards, interceptors, models, services (one per API area) |
| `src/app/layout/shell` | sidebar + top bar, and the routes of the signed-in area |
| `src/app/features` | the pages: analytics, people, recruitment, ai, admin, me, careers, auth |
| `src/app/shared` | reusable pieces: icon, page header, stat card, status badge, markdown pipe, chart theme, helpers |
| `src/styles.css` | the design system (cards, buttons, tables, tabs, badges, alerts) |
