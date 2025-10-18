import os
import requests
import json
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
import io
import contextlib

# --- Configuration ---
os.environ["OPENAI_API_KEY"] = os.environ.get("GAIA_NODE_API_KEY", "dummy_key")
os.environ["OPENAI_API_BASE"] = os.environ.get("GAIA_NODE_URL", "http://localhost:8080/v1")
os.environ["OPENAI_MODEL_NAME"] = os.environ.get("GAIA_NODE_MODEL", "openai/gpt-4")

BLOCKFROST_API_KEY = os.environ.get("BLOCKFROST_API_KEY")
CARDANO_NETWORK = os.environ.get("CARDANO_NETWORK", "preprod")
BLOCKFROST_API_URL = f"https://cardano-{CARDANO_NETWORK}.blockfrost.io/api/v0"


# --- Custom Tool for Fetching On-Chain Data ---
def get_wallet_data(wallet_address: str) -> str:
    if not BLOCKFROST_API_KEY:
        return json.dumps({"error": "Server configuration error: BLOCKFROST_API_KEY is not set."})
    headers = {"project_id": BLOCKFROST_API_KEY}
    data_summary = {}
    TRANSACTION_COUNT = 10
    ASSET_COUNT = 15
    print(f"\n--- [Veritas AI Debug] Starting MINIMAL data fetch for {wallet_address} ---")
    try:
        address_info_url = f"{BLOCKFROST_API_URL}/addresses/{wallet_address}"
        addr_response = requests.get(address_info_url, headers=headers)
        if addr_response.status_code != 200:
            return json.dumps({"error": f"Failed to get address info (Status: {addr_response.status_code}). Is the wallet address correct and on the '{CARDANO_NETWORK}' network?"})
        stake_address = addr_response.json().get('stake_address')
        print(f"--> Fetching last {TRANSACTION_COUNT} transactions...")
        tx_history_url = f"{BLOCKFROST_API_URL}/addresses/{wallet_address}/transactions?order=desc&count={TRANSACTION_COUNT}"
        tx_response = requests.get(tx_history_url, headers=headers)
        tx_response.raise_for_status()
        data_summary['recent_transaction_hashes'] = [tx['tx_hash'] for tx in tx_response.json()]
        if stake_address:
            print(f"--> Fetching first {ASSET_COUNT} assets...")
            assets_url = f"{BLOCKFROST_API_URL}/accounts/{stake_address}/addresses/assets"
            assets_response = requests.get(assets_url, headers=headers)
            assets_response.raise_for_status()
            assets_data = assets_response.json()
            data_summary['assets_held'] = [asset['unit'] for asset in assets_data[:ASSET_COUNT]]
            data_summary['total_asset_classes'] = len(assets_data)
        else:
            data_summary['assets_held'] = []
            data_summary['total_asset_classes'] = 0
        print("--- [Veritas AI Debug] Minimal data fetch completed successfully ---\n")
        return json.dumps(data_summary, indent=2)
    except Exception as e:
        return json.dumps({"error": f"An unexpected error occurred during data fetch: {e}"})


# --- Crew Definition ---
class WalletProfilingCrew:
    def __init__(self, wallet_address: str):
        self.wallet_address = wallet_address
        self.llm = ChatOpenAI(model=os.environ["OPENAI_MODEL_NAME"], base_url=os.environ["OPENAI_API_BASE"], request_timeout=120)

    def run(self):
        from pydantic import BaseModel
        class Result(BaseModel):
            raw: str

        raw_onchain_data = get_wallet_data(self.wallet_address)
        try:
            data_json = json.loads(raw_onchain_data)
            if 'error' in data_json:
                error_message = f"Could not generate profile. Reason: {data_json['error']}"
                return {"result": Result(raw=error_message), "log": error_message}
        except json.JSONDecodeError:
            error_message = "Could not generate profile due to invalid data format from the source."
            return {"result": Result(raw=error_message), "log": error_message}

        # --- Define Agents ---
        data_collector = Agent(role='Cardano On-Chain Data Collector', goal=f'Use the provided data string for the wallet address: {self.wallet_address}.', backstory="You are a data handler. Your only job is to receive raw on-chain data and pass it to the other agents.", verbose=True, allow_delegation=False, llm=self.llm)
        analyst = Agent(role='Expert Crypto Wallet Analyst', goal='Analyze the collected on-chain data to create a clear, bullet-point summary of the wallet\'s profile.', backstory="You are a succinct on-chain analyst. You turn raw data into simple, insightful bullet points for non-technical users. You focus only on the persona and activity.", verbose=True, allow_delegation=False, llm=self.llm)
        security_analyst = Agent(role='On-Chain Security Heuristics Analyst', goal='Scan wallet data for potential red flags or unusual activity patterns based on a set of heuristics. Your analysis must be objective and based only on the data provided.', backstory="You are a security-conscious on-chain analyst. Your job is to find patterns that, while not definitively malicious, are worth a second look. You are cautious but not alarmist.", verbose=True, allow_delegation=False, llm=self.llm)
        
        # --- Define Tasks ---
        data_collection_task = Task(
            description=f"This is the raw on-chain data for wallet {self.wallet_address}:\n\n{raw_onchain_data}",
            expected_output="A confirmation that the data has been processed and is ready for analysis.",
            agent=data_collector
        )

        analysis_task = Task(
            description=(
                "You are an on-chain analyst. Analyze the provided JSON data which contains 'recent_transaction_hashes', 'assets_held', and 'total_asset_classes'. "
                "Your task is to create a very brief, bullet-point summary under the heading '### Wallet Profile'. "
                "Based *only* on the data provided, answer the following:\n"
                "- **Primary Activity:** Does this wallet seem more focused on simple transactions or collecting many different assets (tokens/NFTs)?\n"
                "- **Asset Diversity:** Based on the 'total_asset_classes' count, briefly comment on the number of different assets held (e.g., 'low', 'medium', 'high').\n"
                "- **Wallet Persona:** In one short sentence, what is this wallet's likely persona? (e.g., 'A simple transaction wallet.', 'An active token collector.')"
            ),
            expected_output="A concise, Markdown-formatted, bullet-point summary under the heading '### Wallet Profile'.",
            agent=analyst,
        )

        security_task = Task(
            description=(
                "You will be given a 'Wallet Profile' analysis as context. Your primary job is to perform a security analysis on the same raw data. "
                "Create your analysis as a bullet-point list under the heading '### Security Observations'.\n"
                "Based *only* on the data, consider the following:\n"
                "- **Token Dust:** Does the 'total_asset_classes' number seem high (e.g., greater than 10)?\n"
                "- **Transaction Velocity:** Does the wallet have a full list of 10 recent transactions?\n"
                "- **Overall Risk Profile:** Provide a one-sentence summary of the potential risk profile.\n\n"
                "**IMPORTANT:** Your final output MUST include the original 'Wallet Profile' analysis first, followed by your 'Security Observations' section."
            ),
            expected_output="The complete, combined final report containing BOTH the '### Wallet Profile' section from the context and your new '### Security Observations' section.",
            agent=security_analyst,
            context=[analysis_task]
        )

        # --- Assemble and Run Crew ---
        crew = Crew(
            agents=[data_collector, analyst, security_analyst],
            tasks=[data_collection_task, analysis_task, security_task], # The order matters
            process=Process.sequential,
            verbose=True
        )

        # --- Capture agent logs ---
        log_stream = io.StringIO()
        with contextlib.redirect_stdout(log_stream):
            result = crew.kickoff()
        
        log_contents = log_stream.getvalue()
        
        # --- Return both result and logs ---
        return {"result": result, "log": log_contents}