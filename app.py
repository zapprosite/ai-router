from fastapi import FastAPI

app = FastAPI()

# Minimal endpoints always available
@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/v1/models")
def list_models():
    # Placeholder list; extend to include local/cloud models when available
    return {"data": []}


# Optionally include extra routes if present
try:
    from router_routes import router as rr  # type: ignore
    app.include_router(rr)
except Exception as e:
    @app.get("/healthz/debug")
    def healthz_debug():
        return {"ok": True, "note": str(e)}
