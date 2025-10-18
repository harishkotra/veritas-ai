import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uuid
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from crew_definition import WalletProfilingCrew

jobs = {}

class Job(BaseModel):
    job_id: str
    status: str
    result: str | None = None
    log: str | None = None

class StartJobInput(BaseModel):
    wallet_address: str

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

def run_crew_in_background(job_id: str, wallet_address: str):
    """This function runs the CrewAI task in the background to avoid blocking the API."""
    try:
        jobs[job_id].status = "running"
        crew = WalletProfilingCrew(wallet_address=wallet_address)
        
        # The crew.run() method will now return a dictionary
        response_data = crew.run() # Get the full response object
        
        jobs[job_id].status = "completed"
        # The final report from the agents
        jobs[job_id].result = response_data["result"].raw 
        # The captured console log of the agent's process
        jobs[job_id].log = response_data["log"] 

    except Exception as e:
        jobs[job_id].status = "failed"
        jobs[job_id].result = f"An error occurred: {e}"
        jobs[job_id].log = f"Error during execution: {e}"


@app.get("/input_schema", summary="Get Input Schema")
def get_input_schema():
    """Returns the JSON schema for the input data required to start a job."""
    return {
        "type": "object",
        "properties": {
            "wallet_address": {
                "type": "string",
                "description": "The Cardano wallet address (addr1...) to be analyzed."
            }
        },
        "required": ["wallet_address"]
    }

@app.post("/start_job", response_model=Job, summary="Start a Wallet Profiling Job")
def start_job(request: StartJobRequest, background_tasks: BackgroundTasks):
    """
    Starts a new AI-powered analysis for the given Cardano wallet address.
    """
    wallet_address = request.input_data.wallet_address
    
    if not wallet_address or not (wallet_address.startswith("addr1") or wallet_address.startswith("addr_test1")):
        raise HTTPException(status_code=400, detail="A valid Cardano wallet address (addr1... or addr_test1...) is required.")

    job_id = str(uuid.uuid4())
    jobs[job_id] = Job(job_id=job_id, status="pending")

    # Run the time-consuming AI task in the background
    background_tasks.add_task(run_crew_in_background, job_id, wallet_address)

    return jobs[job_id]

@app.get("/status", response_model=Job, summary="Check Job Status")
def get_status(job_id: str):
    """Retrieves the status and result of a previously started job."""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)