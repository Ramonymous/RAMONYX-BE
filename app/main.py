from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, inventory, production, products, purchasing, sales, users, warehouse

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description=(
        "Backend API untuk sistem ERP dengan fitur inventory, "
        "production, purchasing, dan sales"
    ),
    version="1.0.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/api/v1", tags=["authentication"])
app.include_router(products.router, prefix="/api/v1", tags=["products"])
app.include_router(sales.router, prefix="/api/v1", tags=["sales"])
app.include_router(inventory.router, prefix="/api/v1/inventory", tags=["inventory"])
app.include_router(purchasing.router, prefix="/api/v1/purchasing", tags=["purchasing"])
app.include_router(production.router, prefix="/api/v1/production", tags=["production"])
app.include_router(warehouse.router, prefix="/api/v1/warehouse", tags=["warehouse"])
app.include_router(users.router, prefix="/api/v1/users", tags=["user management"])


@app.get("/")
async def root():
    """Root endpoint with API information"""
    response = {
        "message": "ERP Backend API",
        "version": "1.0.0",
        "environment": settings.app_env,
    }

    if settings.is_development:
        response.update({"docs": "/docs", "redoc": "/redoc"})

    return response


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)  # nosec B104 - development server only
