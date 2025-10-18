# --- START OF FINAL ui.py ---

import streamlit as st
import requests
import time
import os
import json # Import json for pretty printing

# --- Configuration ---
# Configure the URL of your running FastAPI backend
API_BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# --- Helper Functions to Interact with the API ---

def start_analysis_job(input_data: dict):
    """Sends a request to the backend to start a new analysis job."""
    payload = {"input_data": input_data}
    
    # ✨ DEBUGGING: Print the exact payload being sent to the terminal
    st.write("---")
    st.write(f"**Debug Info:** Sending the following payload to `{API_BASE_URL}/start_job`")
    st.code(json.dumps(payload, indent=2), language="json")
    
    try:
        response = requests.post(f"{API_BASE_URL}/start_job", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if e.response:
            st.error(f"Error from server ({e.response.status_code}): Failed to start job. Server says: {e.response.text}")
        else:
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

st.title("Veritas AI 🤖")
st.markdown("An AI-Powered On-Chain Analyst for the Cardano Ecosystem. Choose your analysis mode below.")

tab1, tab2 = st.tabs(["👤 Single Wallet Analysis", "⚔️ Wallet Duel"])

with tab1:
    st.subheader("Profile a single wallet for activity and security insights.")
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
            if st.button(name, on_click=set_wallet_input, args=(address,), use_container_width=True, key=f"example_{i}"):
                pass

    wallet_address_input = st.text_input("Enter Cardano wallet address (preprod)", key="wallet_input", placeholder="addr_test1...")
    analyze_button = st.button("Analyze Wallet", type="primary", key="analyze_single")

    if analyze_button and wallet_address_input:
        st.session_state.pop('last_result', None)
        st.session_state.pop('last_log', None)
        st.session_state.pop('analyzed_wallet', None)
        
        job_response = start_analysis_job({"wallet_address_1": wallet_address_input, "wallet_address_2": None})
        
        if job_response and job_response.get("job_id"):
            job_id = job_response["job_id"]
            with st.spinner("The AI agents are analyzing the wallet... This may take a minute."):
                while True:
                    status_response = get_job_status(job_id)
                    if not status_response: break
                    status = status_response.get("status")
                    if status == "completed":
                        st.success("Analysis Complete!")
                        st.session_state.update(last_result=status_response.get("result"), last_log=status_response.get("log"), analyzed_wallet=wallet_address_input)
                        break
                    elif status == "failed":
                        st.error(f"Analysis failed: {status_response.get('result')}")
                        st.session_state.update(last_log=status_response.get('log'))
                        break
                    time.sleep(2)

with tab2:
    st.subheader("Compare two wallets to see how they stack up.")
    col1, col2 = st.columns(2)
    with col1:
        wallet_1_duel = st.text_input("Enter Wallet Address #1", placeholder=example_wallets["Active NFT Collector"], key="duel1")
    with col2:
        wallet_2_duel = st.text_input("Enter Wallet Address #2", placeholder=example_wallets["Simple Transaction Wallet"], key="duel2")

    compare_button = st.button("Compare Wallets", type="primary", key="analyze_duel")

    if compare_button and wallet_1_duel and wallet_2_duel:
        st.session_state.pop('last_result', None)
        st.session_state.pop('last_log', None)
        st.session_state.pop('analyzed_wallet', None)

        job_response = start_analysis_job({"wallet_address_1": wallet_1_duel, "wallet_address_2": wallet_2_duel})
        
        if job_response and job_response.get("job_id"):
            job_id = job_response["job_id"]
            with st.spinner("The AI agent is comparing the wallets... This may take a minute."):
                while True:
                    status_response = get_job_status(job_id)
                    if not status_response: break
                    status = status_response.get("status")
                    if status == "completed":
                        st.success("Comparison Complete!")
                        st.session_state.update(last_result=status_response.get("result"), last_log=status_response.get("log"), analyzed_wallet="duel_report")
                        break
                    elif status == "failed":
                        st.error(f"Comparison failed: {status_response.get('result')}")
                        st.session_state.update(last_log=status_response.get('log'))
                        break
                    time.sleep(2)

if 'last_result' in st.session_state and st.session_state['last_result']:
    st.subheader("Analysis Result")
    st.download_button(label="📥 Download Report", data=st.session_state['last_result'], file_name=f"veritas_ai_report_{st.session_state.get('analyzed_wallet', 'analysis')}.md", mime='text/markdown')
    st.markdown(st.session_state['last_result'])
    if 'last_log' in st.session_state and st.session_state['last_log']:
        with st.expander("Show Agent Thought Process"):
            st.code(st.session_state['last_log'], language='text')

st.markdown("---")
st.markdown("Powered by [Masumi](https://masumi.anetwork), [Gaia Nodes](https://www.gaianet.ai), and [CrewAI](https://crewai.com).")
st.markdown("Built by [Harish Kotra](https://github.com/harishkotra)")