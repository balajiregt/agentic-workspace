# QA Dashboard Viewer

Static, client-side viewer for generated Agentic QA artifacts.

It is designed for public/demo hosting on Netlify without backend storage:

- uploaded files are parsed in the browser only,
- no files are sent to a server,
- no database or login is required,
- bundle size stays small and dependency-free.

## Supported Artifacts

Upload any of these generated files:

```text
artifacts/qa-dashboard/dashboard.json
artifacts/qa-dashboard-negative/dashboard.json
artifacts/test-graph/test-graph.json
graphify-out/graph.json
artifacts/qa-dashboard/index.html
artifacts/test-graph/index.html
graphify-out/graph.html
```

JSON artifacts render as metrics, coverage, duplicate, and graph views.
HTML artifacts render as sandboxed previews.

## Local Run

```bash
npm --prefix projects/qa-dashboard-viewer run dev
open http://127.0.0.1:8790
```

## Netlify

Create a new Netlify project with:

```text
Base directory: projects/qa-dashboard-viewer
Build command: npm run build
Publish directory: .
```

The viewer is safe for a free/static deployment because user artifacts remain
local to their browser session.
