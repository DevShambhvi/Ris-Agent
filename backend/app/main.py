from fastapi import FastAPI  # type: ignore

app = FastAPI(
    title="Razorpay Risk Investigation System",
    description="AI-assisted payment risk investigation platform",
    version="0.1.0"
)


@app.get("/")
def root():
    return {
        "message": "Razorpay Risk Investigation System is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }