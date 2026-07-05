import sys
import uvicorn

def main():
    print("--- KiwiSDR AI Listener Dashboard ---")
    print("Iniciando servidor web na porta 8000...")
    
    # Run Uvicorn programmatically
    uvicorn.run("src.web.server:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
