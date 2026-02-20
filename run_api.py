import uvicorn
from tracks.config import settings

def main():
    """Run the FastAPI server using uvicorn."""
    print(f"Starting API server on {settings.SERVER_HOST}:{settings.SERVER_PORT}")
    
    uvicorn.run(
        "tracks.app:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=False,
    )

if __name__ == "__main__":
    main()
