from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import inventory, users

app = FastAPI(
    title="V6ss API",
    description="FastAPI layer for the Finished Goods Management System",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(inventory.router, prefix="/api/v1/inventory", tags=["Inventory"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
