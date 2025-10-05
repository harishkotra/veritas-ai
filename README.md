# Veritas AI

An AI-Powered On-Chain Analyst for the Cardano Ecosystem. Veritas AI transforms raw, complex blockchain data into clear, human-readable insights.

# [Project Presentation/Video](https://youtu.be/ycd8y3myxhA)

## Screenshots

<img width="1501" height="1114" alt="Screenshot at Oct 05 21-33-21" src="https://github.com/user-attachments/assets/483564a8-6579-4b34-92e7-5711e0bae039" />
<img width="1499" height="1052" alt="Screenshot at Oct 05 21-33-41" src="https://github.com/user-attachments/assets/44a3e8c7-f8e4-4de9-8530-fd0575de37b6" />
<img width="1500" height="634" alt="Screenshot at Oct 05 21-33-50" src="https://github.com/user-attachments/assets/642a99df-2efb-4bab-8866-aab07ffc557e" />

## 📜 Project Description

The Cardano blockchain is a rich source of data, but understanding the activity of a specific wallet requires sifting through transaction hashes, asset IDs, and on-chain metadata. This process is time-consuming and requires technical expertise.

**Veritas AI** solves this problem by acting as an intelligent on-chain agent. Users can provide any Cardano wallet address, and the agent will perform a detailed analysis, returning a simple, narrative summary of that wallet's profile and activities. It leverages a small, locally-hosted Language Model via Gaia Nodes to ensure data privacy and demonstrates a powerful, decentralized AI architecture.

## ✨ Core Features (Current)

-   **AI-Powered Wallet Profiling:** Provide any `preprod` or `mainnet` Cardano wallet address.
-   **Human-Readable Insights:** The agent analyzes recent transactions and asset holdings to generate a concise, bullet-point summary.
-   **Wallet Persona Identification:** The AI determines the likely persona of the wallet (e.g., "simple transaction wallet," "active token collector," etc.).
-   **Agentic Service via Masumi:** The entire service is built as a monetizable AI Agent on the Masumi Network, ready to accept payments in ADA for its analysis.

## 🛠️ Tech Stack

-   **AI Framework:**
    -   **Masumi Network:** For the agentic framework, decentralized registry, and payment processing.
    -   **CrewAI:** To orchestrate the collaboration between specialized AI agents (a "Data Collector" and an "Analyst").
-   **AI Inference:**
    -   **Gaia Nodes:** For serving a Qwen3-4B LLM with an OpenAI-compatible API, enabling private and decentralized AI inference.
-   **Blockchain & Data:**
    -   **Cardano:** The target blockchain for all on-chain analysis.
    -   **Blockfrost API:** For efficiently fetching on-chain data like transaction histories and asset lists.
-   **Backend & API:**
    -   **Python:** The core programming language for the agent.
    -   **FastAPI:** For exposing the AI agent's capabilities via a robust, modern API.
    -   **NodeJS + TypeScript (for Masumi/MeshSDK):** Underpins the payment and wallet interaction services required by the Masumi Network.

## ⚙️ How It Works (Architecture)

The agent follows a simple but powerful workflow:

1.  **API Request:** A user submits a Cardano wallet address to the `/start_job` endpoint.
2.  **Data Fetching:** The agent's `get_wallet_data` tool makes a call to the Blockfrost API to retrieve a minimal set of recent transactions and asset holdings for that address.
3.  **Crew Orchestration:** The `WalletProfilingCrew` is initiated.
    -   The **Data Collector Agent** receives the raw on-chain data.
    -   The **Analyst Agent** receives the data from the collector along with a specific prompt guiding its analysis.
4.  **AI Inference:** The Analyst Agent sends the data and the prompt to the **Gaia Node LLM**. The model processes the information and generates the bullet-point summary.
5.  **Job Completion:** The FastAPI server stores the result, which can then be retrieved via the `/status` endpoint.

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
uv pip install crewai langchain-openai fastapi uvicorn requests python-dotenv
```

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
PAYMENT_API_KEY=your_masumi_payment_key_here
AGENT_IDENTIFIER=your_agent_identifier_from_registration
PAYMENT_AMOUNT=2000000
PAYMENT_UNIT=lovelace
SELLER_VKEY=your_PREPROD_selling_wallet_vkey_from_masumi

# --- Veritas AI Services ---
CARDANO_NETWORK=preprod # or "mainnet"
BLOCKFROST_API_KEY="your_PREPROD_blockfrost_api_key_here"

# --- Gaia Node AI Inference ---
GAIA_NODE_URL="http://YOUR_GAIA_NODE.gaia.domains/v1"
GAIA_NODE_MODEL="openai/your_model_name" # The openai/ prefix is important!
```

### 4. Run the Agent

Start the FastAPI server:

```bash
python main.py
```

The API will be available at `http://localhost:8000`.

### 5. API Usage

#### Start an Analysis Job

```bash
curl -X POST "http://localhost:8000/start_job" \
-H "Content-Type: application/json" \
-d '{
    "input_data": {
        "wallet_address": "addr_test1wzylc3gg4h37gt69yx057gkn4egefs5t9rsycmryecpsenswtdp58"
    }
}'
```

This will return a `job_id`.

#### Check Job Status

```bash
curl -X GET "http://localhost:8000/status?job_id=YOUR_JOB_ID_HERE"
```

When the `status` is `completed`, the `result` field will contain the AI-generated analysis.

## 🛣️ Next Steps & Future Roadmap

This project is the foundational step for a much larger vision. The next steps are:

-   **🤖 Telegram Bot Integration:** Create a user-friendly Telegram bot that allows anyone to analyze a wallet by simply sending a message. This will serve as the primary user interface.

-   **🌐 Simple Web UI:** Develop a single-page web application as an alternative interface for users who prefer a browser-based experience.

-   **💡 Nucast Track Feature - "Insight-as-IP" NFTs:**
    -   Allow users to mint the AI-generated analysis as an NFT on Cardano.
    -   The NFT metadata will contain the analysis text and a timestamp, creating a verifiable, on-chain record of the AI's insight. This directly combines AI with Intellectual Property innovation on the blockchain.

-   **🏛️ SyncAI Track Feature - DAO Treasury Reporting:**
    -   Extend the agent to analyze DAO treasury wallets.
    -   It will be able to answer natural language questions like, "Generate a weekly spending report for our treasury" or "What are the largest outflows this month?". This provides a powerful tool for decentralized governance and transparency.

-   **🧠 Expand AI Capabilities:**
    -   **Transaction Tagging:** Train the AI to categorize transactions (e.g., "DeFi Swap," "NFT Mint," "Staking Reward").
    -   **Trend Analysis:** Enable the agent to identify trends, such as which tokens a wallet is accumulating over time.
