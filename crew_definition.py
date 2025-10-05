import os
import requests
import json
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

# --- Configuration ---
# Point to your Gaia Node's OpenAI-compatible API
os.environ["OPENAI_API_KEY"] = os.environ.get("GAIA_NODE_API_KEY", "dummy_key")
os.environ["OPENAI_API_BASE"] = os.environ.get("GAIA_NODE_URL", "http://localhost:8080/v1")
os.environ["OPENAI_MODEL_NAME"] = os.environ.get("GAIA_NODE_MODEL", "openai/gpt-4")

# Blockfrost API Configuration
BLOCKFROST_API_KEY = os.environ.get("BLOCKFROST_API_KEY")
CARDANO_NETWORK = os.environ.get("CARDANO_NETWORK", "mainnet")
BLOCKFROST_API_URL = f"https://cardano-{CARDANO_NETWORK}.blockfrost.io/api/v0"


# --- Custom Tool for Fetching On-Chain Data ---
def get_wallet_data(wallet_address: str) -> str:
    """
    Fetches a *minimal* set of transaction history and asset data for a
    Cardano wallet, optimized for small LLMs.
    """
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
            return json.dumps({"error": f"Failed to get address info (Status: {addr_response.status_code})."})
        
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
        else:
            data_summary['assets_held'] = []

        print("--- [Veritas AI Debug] Minimal data fetch completed successfully ---\n")
        return json.dumps(data_summary, indent=2)

    except Exception as e:
        return json.dumps({"error": f"An unexpected error occurred during data fetch: {e}"})


# --- Crew Definition ---
class WalletProfilingCrew:
    def __init__(self, wallet_address: str):
        self.wallet_address = wallet_address
        self.llm = ChatOpenAI(
            model=os.environ["OPENAI_MODEL_NAME"],
            base_url=os.environ["OPENAI_API_BASE"],
            request_timeout=120
        )

    def run(self):
        # Define Agents
        data_collector = Agent(
            role='Cardano On-Chain Data Collector',
            goal=f'Use the provided data string for the wallet address: {self.wallet_address}.',
            backstory="You are a data handler. Your only job is to receive raw on-chain data and pass it to the analyst.",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

        analyst = Agent(
            role='Expert Crypto Wallet Analyst',
            goal='Analyze the collected on-chain data to create a clear, bullet-point summary of the wallet\'s profile.',
            backstory="You are a succinct on-chain analyst. You turn raw data into simple, insightful bullet points for non-technical users.",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        # Get Data
        raw_onchain_data = get_wallet_data(self.wallet_address)
        try:
            data_json = json.loads(raw_onchain_data)
            if 'error' in data_json:
                return f"Could not generate profile. Reason: {data_json['error']}"
        except json.JSONDecodeError:
            return "Could not generate profile due to invalid data format from the source."

        # Define Tasks
        data_collection_task = Task(
            description=f"This is the raw on-chain data for wallet {self.wallet_address}:\n\n{raw_onchain_data}",
            expected_output="A confirmation that the data has been passed to the analyst.",
            agent=data_collector
        )

        analysis_task = Task(
            description=(
                "You are an on-chain analyst. Analyze the provided JSON data which contains 'recent_transaction_hashes' and 'assets_held'. "
                "Your task is to create a very brief, bullet-point summary. "
                "Based *only* on the data provided, answer the following:\n"
                "- **Primary Activity:** Does this wallet seem more focused on simple transactions or collecting many different assets (tokens/NFTs)?\n"
                "- **Asset Diversity:** Briefly comment on the number of different assets held (e.g., 'low', 'medium', 'high').\n"
                "- **Wallet Persona:** In one short sentence, what is this wallet's likely persona? (e.g., 'A simple transaction wallet.', 'An active token collector.')"
            ),
            expected_output="A concise, bullet-point summary answering the three specific questions.",
            agent=analyst
        )

        # Assemble and Run Crew
        crew = Crew(
            agents=[data_collector, analyst],
            tasks=[data_collection_task, analysis_task],
            process=Process.sequential,
            verbose=True
        )

        result = crew.kickoff()
        return result