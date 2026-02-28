#!/usr/bin/env python3
"""
LitePolis Backend Server for E2E Testing

Run this script to start the LitePolis backend server.
The server will be available at http://localhost:8000
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the router from litepolis_router_default
from litepolis_router_default.core import router

app = FastAPI(
    title="LitePolis API",
    description="Polis-compatible API implementation",
    version="0.1.0"
)

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include router with /api/v3 prefix
app.include_router(router, prefix="/api/v3")


@app.get("/")
async def root():
    return {"message": "LitePolis API Server", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import os
    port = int(os.environ.get("LITEPOLIS_PORT", 8000))
    print(f"Starting LitePolis Backend Server on http://localhost:{port}")
    print(f"API endpoints available at http://localhost:{port}/api/v3/")
    uvicorn.run(app, host="0.0.0.0", port=port)
