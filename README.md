# 🌌 Strategy Analysis Platform V2
### *High-Performance Quantitative Intelligence & ML Training Ecosystem*

[![Shared Core CI](https://github.com/NeoNix-Lab/StrategyAnalysisPlatform/actions/workflows/quant-shared-ci.yml/badge.svg)](https://github.com/NeoNix-Lab/StrategyAnalysisPlatform/actions/workflows/quant-shared-ci.yml) [![API Gateway CI](https://github.com/NeoNix-Lab/StrategyAnalysisPlatform/actions/workflows/api_gateway-ci.yml/badge.svg)](https://github.com/NeoNix-Lab/StrategyAnalysisPlatform/actions/workflows/api_gateway-ci.yml) [![ML Core CI](https://github.com/NeoNix-Lab/StrategyAnalysisPlatform/actions/workflows/ml_core-ci.yml/badge.svg)](https://github.com/NeoNix-Lab/StrategyAnalysisPlatform/actions/workflows/ml_core-ci.yml) [![Frontend CI](https://github.com/NeoNix-Lab/StrategyAnalysisPlatform/actions/workflows/frontend-ci.yml/badge.svg)](https://github.com/NeoNix-Lab/StrategyAnalysisPlatform/actions/workflows/frontend-ci.yml)

**Strategy Analysis Platform V2** is a professional-grade, event-first monorepo designed for institutional-level algorithmic trading analytics. By decoupling high-speed data ingestion from complex quantitative modeling and machine learning workflows, the platform provides a scalable, real-time environment for alpha discovery and strategy optimization.

---

## 💎 Key Features & Capabilities

### ⚡ Real-Time Event Streaming & Ingestion
*   **Institutional Connectors**: Native C# exporters for **Quantower** provide sub-millisecond event streaming of orders, executions, and price action directly to the analytics engine.
*   **Event-First Architecture**: Every movement in the trading lifecycle is captured as a discrete event, ensuring 100% data integrity and eliminating the need for bulky, error-prone manual exports.

### 🧠 Advanced Quantitative Intelligence
*   **Precision Trade Reconstruction**: Sophisticated algorithms automatically reconstruct trades from raw execution logs, handling complex scaling, partial fills, and varying lot sizes.
*   **Professional Metrics Suite**: Instant calculation of institutional-grade KPIs, including:
    *   **Performance**: Net PnL, Win Rate, Profit Factor, and Sharpe Ratio.
    *   **Risk**: Dynamic Drawdown analysis and Stability R2 metrics.
    *   **Efficiency**: Advanced **MAE/MFE** (Maximum Adverse/Favorable Excursion) per-trade analysis to identify optimal stop and target levels.
*   **Regime Detection**: Integrated quantitative models to identify market states (Trending vs. Ranging), allowing for context-aware performance analysis.

### 🧪 ML Studio: The Future of Strategy Development
*   **Reward Designer**: A visual interface to define complex reward functions based on PnL, risk-adjusted returns, or custom quantitative signals.
*   **Neuro-Architect**: Design custom neural network architectures (LSTMs, CNNs, MLPs) directly through the platform to power your RL agents.
*   **Asynchronous Training Node**: A dedicated microservice for high-performance training. Scale horizontally using specialized GPU hardware while maintaining a responsive user experience.
*   **EnvFlex Environment**: A proprietary, highly flexible RL environment that enables agents to interact with historical market data with realistic execution constraints.

### � Professional-Grade Cockpit
*   **Dynamic Visualizations**: Real-time equity curves, trade clusters, and distribution charts powered by Recharts and high-performance financial charting libraries.
*   **Stress Testing**: Integrated modules to evaluate strategy robustness under simulated adverse conditions.
*   **Setups Analysis**: Visualize entries and exits on top of actual price action to identify behavioral patterns and edge cases.

---

## 🏗️ Technical Architecture (Monorepo)

### 📦 The Core Engine (`quant_shared`)
The bedrock of the platform. A shared Python library implementing the unified data layer (SQLAlchemy), quantitative logic, and schema definitions used by all microservices.

### 🚀 Scalable Microservices
*   **API Gateway**: The high-performance entry point managing traffic, authentication, and the real-time ingestion pipeline.
*   **ML Core**: A dedicated microservice built on TensorFlow/Keras, optimized for intensive machine learning training and inference.
*   **Training Node**: The specialized engine for Reinforcement Learning execution.

### � Modern Frontend
A high-performance React application built with Vite, offering a lightning-fast UI and an intuitive "ML-Studio" experience for strategy designers.

---

## 🛠️ Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- .NET 8 SDK

### 1. Python Environment Setup
We use a single shared virtual environment at the root of the project to manage all services.

```bash
# From the project root (Main/)
python -m venv .venv
# Windows: .venv\Scripts\Activate | Linux/macOS: source .venv/bin/activate

# Install shared package first in editable mode
pip install -e packages/quant_shared

# Install service dependencies
pip install -e services/api_gateway
pip install -e services/ml_core
```

### 2. Running the Backend
```bash
# Start the API Gateway
# Ensure your PYTHONPATH includes the services/api_gateway/src directory
uvicorn api.main:app --host 0.0.0.0 --port 8000 --app-dir services/api_gateway/src
```
Default DB: `trading_data.db` (located at the project root).

### 3. Running the Frontend
```bash
cd frontend/quant_frontend
npm install
npm run dev
```

---

## 🧪 Testing
The CI/CD pipeline runs tests for each component using a matrix strategy:
- **Shared Package**: `pytest packages/quant_shared`
- **API Gateway**: `pytest services/api_gateway`
- **ML Core**: `pytest services/ml_core`
- **Frontend**: `npm test` inside `frontend/quant_frontend`

## 🤖 Automations & Issues
- **GitHub Actions**: Automated CI for Python, .NET, and Node.js.
- **Issue Tracking**: Issues are mirrored locally in `Docs/Issues/` as JSON files for auditability and "Zero Browser" management using `gh` CLI.
- **Database Status**: Root-level `trading_data.db` is the primary SQLite store for development.

## 📄 Documentation Indices
Consult `Docs/` for detailed guides:
- `ARCHITECTURE.md`: Technical overview.
- `Workflow.md`: Terminal-first management guide.
- `Metrics_Implementation_Status.md`: Current coverage of analytics.
