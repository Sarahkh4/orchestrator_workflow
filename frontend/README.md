# Report Forge Frontend

React + Tailwind CSS client for the FastAPI report generator.

## Run locally

From this directory:

```bash
npm install
npm run dev
```

The Vite dev server runs on `http://127.0.0.1:5173` and proxies API calls to the FastAPI backend at `http://127.0.0.1:8000`.

In a separate terminal from the project root, run the backend:

```bash
uvicorn app:app --reload
```

## Build

```bash
npm run build
```
