import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uuid
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

# Import our new crew definition
from crew_definition import WalletProfilingCrew

jobs = {}

class Job(BaseModel):
    job_id: str
    status: str
    result: str | None = None
    log: str | None = None

class StartJobInput(BaseModel):
    wallet_address_1: str
    wallet_address_2: str | None = None

class StartJobRequest(BaseModel):
    input_data: StartJobInput

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Veritas AI Agent...")
    yield
    print("Shutting down Veritas AI Agent.")

app = FastAPI(
    title="Veritas AI Agent",
    description="An AI agent for on-chain Cardano analysis, powered by Masumi and Gaia Nodes.",
    version="0.1.0",
    lifespan=lifespan,
)

def run_crew_in_background(job_id: str, wallet_address_1: str, wallet_address_2: str | None):
    """This function runs the CrewAI task in the background to avoid blocking the API."""
    try:
        jobs[job_id].status = "running"
        crew = WalletProfilingCrew(wallet_address_1=wallet_address_1, wallet_address_2=wallet_address_2)
        response_data = crew.run()
        jobs[job_id].status = "completed"
        jobs[job_id].result = response_data["result"].raw 
        jobs[job_id].log = response_data["log"] 
    except Exception as e:
        jobs[job_id].status = "failed"
        jobs[job_id].result = f"An error occurred: {e}"
        jobs[job_id].log = f"Error during execution: {e}"

@app.post("/start_job", response_model=Job, summary="Start a Wallet Profiling Job")
def start_job(request: StartJobRequest, background_tasks: BackgroundTasks):
    """
    Starts a new AI-powered analysis. Can be a single wallet profile
    or a comparative analysis between two wallets.
    """
    wallet_address_1 = request.input_data.wallet_address_1
    wallet_address_2 = request.input_data.wallet_address_2
    
    if not wallet_address_1 or not (wallet_address_1.startswith("addr1") or wallet_address_1.startswith("addr_test1")):
        raise HTTPException(status_code=400, detail="A valid primary Cardano wallet address (addr1... or addr_test1...) is required.")
    if wallet_address_2 and not (wallet_address_2.startswith("addr1") or wallet_address_2.startswith("addr_test1")):
         raise HTTPException(status_code=400, detail="The second Cardano wallet address is invalid.")

    job_id = str(uuid.uuid4())
    jobs[job_id] = Job(job_id=job_id, status="pending")
    background_tasks.add_task(run_crew_in_background, job_id, wallet_address_1, wallet_address_2)
    return jobs[job_id]

@app.get("/status", response_model=Job, summary="Check Job Status")
def get_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)