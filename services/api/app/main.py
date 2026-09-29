from fastapi import FastAPI

app = FastAPI(title="AgroSentinel API")


@app.get("/health")
def health():
    return {"status": "ok"}
