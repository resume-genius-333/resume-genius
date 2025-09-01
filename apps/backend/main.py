import os
import uvicorn
import asyncio


async def run_fastapi():
    """Run the FastAPI server"""
    # Set NO_PROXY environment variables for local development
    os.environ["NO_PROXY"] = "localhost,127.0.0.1"
    os.environ["no_proxy"] = "localhost,127.0.0.1"
    
    config = uvicorn.Config(
        "src.api.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    # Run FastAPI server
    asyncio.run(run_fastapi())
