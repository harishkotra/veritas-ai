# --- START OF CORRECTED crew_definition.py ---

import os
import requests
import json
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
import io
import contextlib

os.environ["OPENAI_API_KEY"] = os.environ.get("GAIA_NODE_API_KEY", "dummy_key")
os.environ["OPENAI_API_BASE"] = os.environ.get("GAIA_NODE_URL", "http://localhost:8080/v1")
os.environ["OPENAI_MODEL_NAME"] = os.environ.get("GAIA_NODE_MODEL", "openai/gpt-4")

BLOCKFROST_API_KEY = os.environ.get("BLOCKFROST_API_KEY")
CARDANO_NETWORK = os.environ.get("CARDANO_NETWORK", "preprod")
BLOCKFROST_API_URL = f"https://cardano-{CARDANO_NETWORK}.blockfrost.io/api/v0"

def get_wallet_data(wallet_address: str) -> str:
    if not BLOCKFROST_API_KEY: return json.dumps({"error": "Server configuration error: BLOCKFROST_API_KEY is not set."})
    headers = {"project_id": BLOCKFROST_API_KEY}
    data_summary = {}
    TRANSACTION_COUNT, ASSET_COUNT = 10, 15
    print(f"\n--- [Veritas AI Debug] Starting MINIMAL data fetch for {wallet_address} ---")
    try:
        address_info_url = f"{BLOCKFROST_API_URL}/addresses/{wallet_address}"
        addr_response = requests.get(address_info_url, headers=headers)
        if addr_response.status_code != 200: return json.dumps({"error": f"Failed to get address info (Status: {addr_response.status_code}). Is the address on '{CARDANO_NETWORK}'?"})
        stake_address = addr_response.json().get('stake_address')
        tx_history_url = f"{BLOCKFROST_API_URL}/addresses/{wallet_address}/transactions?order=desc&count={TRANSACTION_COUNT}"
        tx_response = requests.get(tx_history_url, headers=headers)
        tx_response.raise_for_status()
        data_summary['recent_transaction_hashes'] = [tx['tx_hash'] for tx in tx_response.json()]
        if stake_address:
            assets_url = f"{BLOCKFROST_API_URL}/accounts/{stake_address}/addresses/assets"
            assets_response = requests.get(assets_url, headers=headers)
            assets_response.raise_for_status()
            assets_data = assets_response.json()
            data_summary['assets_held'] = [asset['unit'] for asset in assets_data[:ASSET_COUNT]]
            data_summary['total_asset_classes'] = len(assets_data)
        else:
            data_summary.update(assets_held=[], total_asset_classes=0)
        return json.dumps(data_summary, indent=2)
    except Exception as e:
        return json.dumps({"error": f"An unexpected error during data fetch: {e}"})

class WalletProfilingCrew:
    def __init__(self, wallet_address_1: str, wallet_address_2: str | None = None):
        self.wallet_address_1 = wallet_address_1
        self.wallet_address_2 = wallet_address_2
        self.llm = ChatOpenAI(model=os.environ["OPENAI_MODEL_NAME"], base_url=os.environ["OPENAI_API_BASE"], request_timeout=120)

    def run(self):
        from pydantic import BaseModel
        class Result(BaseModel):
            raw: str

        # --- DUAL WALLET ANALYSIS MODE ---
        if self.wallet_address_2:
            raw_data_1 = get_wallet_data(self.wallet_address_1)
            raw_data_2 = get_wallet_data(self.wallet_address_2)
            data1_json = json.loads(raw_data_1); data2_json = json.loads(raw_data_2)
            if 'error' in data1_json or 'error' in data2_json:
                error_message = f"Could not generate comparison. Wallet 1 error: {data1_json.get('error', 'None')}, Wallet 2 error: {data2_json.get('error', 'None')}"
                return {"result": Result(raw=error_message), "log": error_message}
            combined_data = f"--- Wallet 1 Data ---\n{raw_data_1}\n\n--- Wallet 2 Data ---\n{raw_data_2}"
            comparative_analyst = Agent(role='Expert Comparative On-Chain Analyst', goal='Analyze and compare the on-chain data from two different Cardano wallets.', backstory="You are an expert in on-chain forensics, specializing in comparing wallet behaviors.", verbose=True, allow_delegation=False, llm=self.llm)
            comparison_task = Task(description=f"Analyze the provided JSON data for two wallets and create a comparative report in Markdown format under the heading '### Wallet Duel Analysis'.\n\n{combined_data}\n\nAnswer the following:\n- **Primary Activity:** How do their primary activities compare?\n- **Asset Diversity:** Which wallet holds more diverse assets?\n- **Activity Level:** Which wallet appears more active?\n- **Overall Comparison:** What is the key difference or similarity between them?", expected_output="A concise, Markdown-formatted, bullet-point summary under the heading '### Wallet Duel Analysis'.", agent=comparative_analyst)
            crew = Crew(agents=[comparative_analyst], tasks=[comparison_task], process=Process.sequential, verbose=True)
        else:
            # Use self.wallet_address_1 now
            raw_onchain_data = get_wallet_data(self.wallet_address_1)
            try:
                data_json = json.loads(raw_onchain_data)
                if 'error' in data_json:
                    error_message = f"Could not generate profile. Reason: {data_json['error']}"
                    return {"result": Result(raw=error_message), "log": error_message}
            except json.JSONDecodeError:
                error_message = "Could not generate profile due to invalid data format from the source."
                return {"result": Result(raw=error_message), "log": error_message}

            # Define Agents
            data_collector = Agent(
                role='Cardano On-Chain Data Collector',
                # Use self.wallet_address_1
                goal=f'Use the provided data string for the wallet address: {self.wallet_address_1}.',
                backstory="You are a data handler. Your only job is to receive raw on-chain data and pass it to the other agents.",
                verbose=True, allow_delegation=False, llm=self.llm
            )
            analyst = Agent(role='Expert Crypto Wallet Analyst', goal='Analyze collected on-chain data to create a clear, bullet-point summary of the wallet\'s profile.', backstory="You are a succinct on-chain analyst who turns raw data into simple insights for non-technical users.", verbose=True, allow_delegation=False, llm=self.llm)
            security_analyst = Agent(role='On-Chain Security Heuristics Analyst', goal='Scan wallet data for potential red flags or unusual activity patterns based on a set of heuristics.', backstory="You are a security-conscious on-chain analyst. You find patterns that are worth a second look.", verbose=True, allow_delegation=False, llm=self.llm)
            
            # Define Tasks
            data_collection_task = Task(
                # Use self.wallet_address_1
                description=f"This is the raw on-chain data for wallet {self.wallet_address_1}:\n\n{raw_onchain_data}",
                expected_output="A confirmation that the data has been processed and is ready for analysis.",
                agent=data_collector
            )
            analysis_task = Task(description=("You are an on-chain analyst. Analyze the provided JSON data. Create a brief, bullet-point summary under the heading '### Wallet Profile'. Answer:\n- **Primary Activity:** Transactions or collecting assets?\n- **Asset Diversity:** Comment on the number of different assets held.\n- **Wallet Persona:** In one short sentence, what is this wallet's likely persona?"), expected_output="A concise, Markdown-formatted, bullet-point summary under the heading '### Wallet Profile'.", agent=analyst)
            security_task = Task(description=("You will be given a 'Wallet Profile' analysis as context. Your job is to perform a security analysis on the same raw data. Create your analysis as a bullet-point list under the heading '### Security Observations'. Consider:\n- **Token Dust:** Is the 'total_asset_classes' number high?\n- **Transaction Velocity:** Is there a full list of recent transactions?\n- **Overall Risk Profile:** Provide a one-sentence summary.\n\n**IMPORTANT:** Your final output MUST include the original 'Wallet Profile' analysis first, followed by your 'Security Observations' section."), expected_output="The complete, combined final report containing BOTH the '### Wallet Profile' and '### Security Observations' sections.", agent=security_analyst, context=[analysis_task])

            # Assemble and Run Crew
            crew = Crew(agents=[data_collector, analyst, security_analyst], tasks=[data_collection_task, analysis_task, security_task], process=Process.sequential, verbose=True)

        log_stream = io.StringIO()
        with contextlib.redirect_stdout(log_stream):
            result = crew.kickoff()
        
        log_contents = log_stream.getvalue()

        final_result_object = Result(raw=str(result))
        
        return {"result": final_result_object, "log": log_contents}