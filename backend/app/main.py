from fastapi import FastAPI

app = FastAPI(title="Compass")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
