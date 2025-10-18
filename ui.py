import streamlit as st
import requests
import time
import os

# --- Configuration ---
# Configure the URL of your running FastAPI backend
API_BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# --- Helper Functions to Interact with the API ---
def start_analysis_job(wallet_address: str):
    """Sends a request to the backend to start a new analysis job."""
    payload = {"input_data": {"wallet_address": wallet_address}}
    try:
        response = requests.post(f"{API_BASE_URL}/start_job", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to connect to the analysis service. Is the backend running? Error: {e}")
        return None

def get_job_status(job_id: str):
    """Polls the backend for the status of a specific job."""
    try:
        response = requests.get(f"{API_BASE_URL}/status", params={"job_id": job_id})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to get job status. Error: {e}")
        return None

# --- Streamlit UI Layout ---
st.set_page_config(page_title="Veritas AI", layout="wide")

# --- Header ---
st.title("Veritas AI 🤖")
st.markdown("An AI-Powered On-Chain Analyst for the Cardano Ecosystem. Enter a wallet address to begin.")

# --- Example Wallets ---
st.subheader("Try an Example")
example_wallets = {
    "Active NFT Collector": "addr_test1qr33ynuc6yg4w56mccww3kcwqn54el84225xhvgkukf6wm32ah6gtt8ca4g0jdjcw50fk5ng5kpuc5uz4qula3gdlywssd3nq3",
    "Simple Transaction Wallet": "addr_test1vzpwq95z3xyum8vqndgdd9mdnmafh3djcxnc6jemlgdmswcve6tkw",
}
if 'wallet_input' not in st.session_state:
    st.session_state['wallet_input'] = ""
def set_wallet_input(address):
    st.session_state['wallet_input'] = address
cols = st.columns(len(example_wallets))
for i, (name, address) in enumerate(example_wallets.items()):
    with cols[i]:
        if st.button(name, on_click=set_wallet_input, args=(address,), use_container_width=True):
            pass

# --- Main Input and Analysis Trigger ---
st.subheader("Analyze a New Wallet")
wallet_address_input = st.text_input(
    "Enter Cardano wallet address (preprod)", 
    key="wallet_input",
    placeholder="addr_test1..."
)
analyze_button = st.button("Analyze Wallet", type="primary")

if analyze_button and wallet_address_input:
    # Clear previous results before starting a new analysis
    st.session_state.pop('last_result', None)
    st.session_state.pop('last_log', None)
    st.session_state.pop('analyzed_wallet', None)

    job_response = start_analysis_job(wallet_address_input)
    if job_response and job_response.get("job_id"):
        job_id = job_response["job_id"]
        with st.spinner("The AI agents are analyzing the wallet... This may take a minute."):
            while True:
                status_response = get_job_status(job_id)
                if not status_response:
                    st.error("Failed to get job status. Halting.")
                    break
                
                status = status_response.get("status")
                if status == "completed":
                    st.success("Analysis Complete!")
                    st.session_state['last_result'] = status_response.get("result")
                    st.session_state['last_log'] = status_response.get("log")
                    # ✨ NEW: Store the wallet address for the filename ✨
                    st.session_state['analyzed_wallet'] = wallet_address_input 
                    break
                elif status == "failed":
                    st.error(f"Analysis failed: {status_response.get('result')}")
                    st.session_state['last_log'] = status_response.get('log')
                    break
                
                time.sleep(2)
    elif not job_response:
        pass
    else:
        st.error("Failed to start the analysis job. Please check the address and try again.")

# --- Display Result ---
if 'last_result' in st.session_state and st.session_state['last_result']:
    st.subheader("Analysis Result")
    st.download_button(
       label="📥 Download Report",
       data=st.session_state['last_result'],
       file_name=f"veritas_ai_report_{st.session_state.get('analyzed_wallet', 'analysis')}.md",
       mime='text/markdown',
    )
    
    st.markdown(st.session_state['last_result'])
    
    if 'last_log' in st.session_state and st.session_state['last_log']:
        with st.expander("Show Agent Thought Process"):
            st.code(st.session_state['last_log'], language='text')

# --- Footer ---
st.markdown("---")
st.markdown("Powered by [Masumi](https://masumi.network), [Gaia Nodes](https://www.gaianet.ai), and [CrewAI](https://crewai.com).")