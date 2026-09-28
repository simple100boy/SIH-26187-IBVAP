import uvicorn
import os
from app.config import HOST, PORT

if __name__ == "__main__":
    print("==================================================================")
    print("  IBVAP - Intelligent Border Video Analytics Platform")
    print("  Starting Command & Control Server on http://localhost:8000")
    print("==================================================================")
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=False)
