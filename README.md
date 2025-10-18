# Veritas AI

An AI-Powered On-Chain Analyst for the Cardano Ecosystem. Veritas AI transforms raw, complex blockchain data into clear, human-readable insights.

# [Project Presentation/Video](https://youtu.be/ycd8y3myxhA)

## Screenshots

#### v2

<img width="1456" height="6299" alt="FireShot Capture 015 - Veritas AI - localhost" src="https://github.com/user-attachments/assets/9e73b7dc-3ab7-422e-b3db-854d862ac7e7" />
<img width="1456" height="4463" alt="FireShot Capture 014 - Veritas AI - localhost" src="https://github.com/user-attachments/assets/fcf42824-9e31-4e7b-8c8d-396e25120491" />
<img width="1456" height="1581" alt="FireShot Capture 013 - Veritas AI - localhost" src="https://github.com/user-attachments/assets/ef16043f-4f29-4678-9df8-f8567a614d8e" />

#### v1
<img width="1501" height="1114" alt="Screenshot at Oct 05 21-33-21" src="https://github.com/user-attachments/assets/483564a8-6579-4b34-92e7-5711e0bae039" />
<img width="1499" height="1052" alt="Screenshot at Oct 05 21-33-41" src="https://github.com/user-attachments/assets/44a3e8c7-f8e4-4de9-8530-fd0575de37b6" />
<img width="1500" height="634" alt="Screenshot at Oct 05 21-33-50" src="https://github.com/user-attachments/assets/642a99df-2efb-4bab-8866-aab07ffc557e" />

## 📜 Project Description

The Cardano blockchain is a rich source of data, but understanding the activity of a specific wallet requires sifting through transaction hashes, asset IDs, and on-chain metadata. This process is time-consuming and requires technical expertise.

**Veritas AI** solves this problem by acting as an intelligent on-chain agent. Users can provide any Cardano wallet address, and the agent will perform a detailed analysis, returning a simple, narrative summary of that wallet's profile and activities. It leverages a small, locally-hosted Language Model via Gaia Nodes to ensure data privacy and demonstrates a powerful, decentralized AI architecture.

## ✨ Core Features (Current)

-   **AI-Powered Wallet Profiling:** Provides a detailed persona and activity summary for any `preprod` or `mainnet` Cardano wallet.
-   **On-Chain Security Analysis:** A specialized security agent scans the wallet for heuristics like token dust and high transaction velocity to provide a risk profile.
-   **Wallet Duel Mode:** A comparative analysis mode where two wallets can be analyzed side-by-side to contrast their activity, diversity, and overall strategy.
-   **Interactive Web UI:** A user-friendly interface built with Streamlit that allows for easy analysis and viewing of the agent's thought process.
-   **Agentic Service via Masumi:** The entire service is built as a monetizable AI Agent on the Masumi Network, ready to accept payments in ADA for its analysis.

## 🛠️ Tech Stack

-   **AI Framework:**
    -   **Masumi Network:** For the agentic framework, decentralized registry, and payment processing.
    -   **CrewAI:** To orchestrate the collaboration between specialized AI agents (a "Data Collector," "Analyst," and "Security Analyst").
-   **AI Inference:**
    -   **Gaia Nodes:** For serving a Qwen3-4B LLM with an OpenAI-compatible API, enabling private and decentralized AI inference.
-   **Blockchain & Data:**
    -   **Cardano:** The target blockchain for all on-chain analysis.
    -   **Blockfrost API:** For efficiently fetching on-chain data like transaction histories and asset lists.
-   **Backend & API:**
    -   **Python:** The core programming language for the agent.
    -   **FastAPI:** For exposing the AI agent's capabilities via a robust, modern API.
    -   **Streamlit:** For the interactive web-based user interface.
    -   **NodeJS + TypeScript (for Masumi/MeshSDK):** Underpins the payment and wallet interaction services required by the Masumi Network.

## ⚙️ How It Works (Architecture)

The agent follows a powerful, conditional workflow:

1.  **User Interaction:** A user interacts with the Streamlit UI, choosing either a single wallet analysis or a two-wallet comparison.
2.  **API Request:** The Streamlit frontend sends a request to the FastAPI `/start_job` endpoint with one or two wallet addresses.
3.  **Data Fetching:** The agent's `get_wallet_data` tool makes calls to the Blockfrost API to retrieve a minimal set of data for each address.
4.  **Crew Orchestration (Conditional):**
    -   **Single Wallet Mode:** A three-agent crew is initiated. The **Data Collector** passes data to the **Wallet Analyst**, who creates a profile. The profile is then passed to the **Security Analyst**, who appends a risk assessment.
    -   **Wallet Duel Mode:** A specialized, single-agent crew is initiated. The **Comparative Analyst** receives data from both wallets and generates a direct comparison.
5.  **AI Inference:** The agents send their data and prompts to the **Gaia Node LLM**. The model processes the information and generates the analysis.
6.  **Job Completion:** The FastAPI server stores the final report and the agent's thought process log, which the Streamlit UI polls for and displays to the user.

## 🚀 Getting Started

Follow these instructions to run Veritas AI on your local machine.

### Prerequisites

-   Python >= 3.10
-   [uv](https://github.com/astral-sh/uv) (a fast Python package manager)
-   A running Masumi Payment Service
-   A running Gaia Node with a loaded language model

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/veritas-ai.git
cd veritas-ai
```

### 2. Install Dependencies

```bash
# Create and activate a virtual environment
uv venv

# On macOS/Linux
source .venv/bin/activate

# On Windows
.venv\Scripts\activate

# Install all required packages
uv pip install crewai langchain-openai fastapi uvicorn requests python-dotenv streamlit```

### 3. Configure Environment Variables

Copy the example environment file and fill it with your credentials.

```bash
cp .env.example .env
```

Now, edit the `.env` file:

```text
# .env

# --- Masumi Payment Service ---
PAYMENT_SERVICE_URL=http://localhost:3001/api/v1
# ... (rest of your .env file)

# --- Veritas AI Services ---
CARDANO_NETWORK=preprod # or "mainnet"
BLOCKFROST_API_KEY="your_PREPROD_blockfrost_api_key_here"

# --- Gaia Node AI Inference ---
GAIA_NODE_URL="http://YOUR_GAIA_NODE.gaia.domains/v1"
GAIA_NODE_MODEL="openai/your_model_name" # The openai/ prefix is important!
```

### 4. Run the Application

You need to run two services in separate terminals.

**Terminal 1: Start the Backend API**

```bash
python main.py
```
The API will be available at `http://localhost:8000`.

**Terminal 2: Start the Web UI**

```bash
streamlit run ui.py
```
A browser window should automatically open to the web interface.

### 5. Using the Web Interface

-   **Single Wallet Analysis:** Use the first tab to analyze a single wallet. You can use the example buttons or paste in a new address. The final report will contain both a "Wallet Profile" and a "Security Observations" section.
-   **Wallet Duel:** Use the second tab to compare two wallets side-by-side.
-   **Agent Thought Process:** After any analysis is complete, an expandable section appears, allowing you to view the raw log of the AI agents' thinking process.
-   **Download Report:** You can download any generated report as a Markdown file.

## 🛣️ Next Steps & Future Roadmap

This project is the foundational step for a much larger vision. The next steps are:

-   **🤖 Telegram Bot Integration:** Create a user-friendly Telegram bot that allows anyone to analyze a wallet by simply sending a message. This will serve as the primary user interface.
-   **🌐 Simple Web UI:** A functional web UI has been implemented with Streamlit, serving as a powerful demonstration and alternative interface.
-   **💡 Nucast Track Feature - "Insight-as-IP" NFTs:**
    -   Allow users to mint the AI-generated analysis as an NFT on Cardano.
    -   The NFT metadata will contain the analysis text and a timestamp, creating a verifiable, on-chain record of the AI's insight. This directly combines AI with Intellectual Property innovation on the blockchain.
-   **🏛️ SyncAI Track Feature - DAO Treasury Reporting:**
    -   Extend the agent to analyze DAO treasury wallets.
    -   It will be able to answer natural language questions like, "Generate a weekly spending report for our treasury" or "What are the largest outflows this month?". This provides a powerful tool for decentralized governance and transparency.
-   **🧠 Expand AI Capabilities:**
    -   **Transaction Tagging:** Train the AI to categorize transactions (e.g., "DeFi Swap," "NFT Mint," "Staking Reward").
    -   **Trend Analysis:** Enable the agent to identify trends, such as which tokens a wallet is accumulating over time.
