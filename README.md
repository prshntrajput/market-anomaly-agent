Market Anomaly Detection Agent

An AI-powered agent that monitors stock markets in real-time, detects anomalies, investigates root causes using web search, and generates detailed reports.


---

Table of Contents

Overview

Features

System Architecture

Prerequisites

Installation

Step 1: Clone Repository

Step 2: Create Virtual Environment

Step 3: Install Dependencies


Configuration

Environment Variables

Obtaining API Keys


Usage

Single Monitoring Cycle

Continuous Monitoring

Monitoring Indian Stocks


How It Works

1. Anomaly Detection

2. Investigation Process

3. Query Generation Strategies

4. Evidence Evaluation

5. Report Generation




---

Overview

This system continuously monitors stock prices, detects significant market anomalies (price drops, volume spikes, etc.), and automatically investigates the root cause using LangGraph agents, web search, and LLM-powered analysis. It then generates detailed professional markdown reports summarizing findings, evidence, and recommendations.


---

Features

✅ Real-time market monitoring for multiple stocks

✅ Multi-factor anomaly detection:

Price change percentage

Volume spike ratio

RSI (Relative Strength Index)

Volatility

Price gaps


✅ AI-powered root cause investigation with self-correction loops

✅ Advanced query generation using:

Chain-of-Thought reasoning

Expert role prompts

Meta-optimization


✅ Evidence evaluation with source credibility scoring

✅ Professional markdown report generation

✅ Continuous monitoring mode with configurable time intervals



---

System Architecture

Market Data (yfinance)
       |
       v
Anomaly Detector (Multi-factor scoring)
       |
       v
Production Monitor
       |
       v
Investigation Agent (LangGraph v5)
       |
       v
+-------------------------------------------+
|               Query Generator             |
|-------------------------------------------|
| - Chain-of-Thought reasoning              |
| - Expert Role Prompts (multi-expert view) |
| - Meta-prompt optimization                |
+-------------------------------------------+
       |
       v
Web Search (Tavily API)
       |
       v
Evidence Evaluator
       |
       v
Report Generator (Markdown)


---

Prerequisites

Python 3.10 or higher

pip (Python package manager)

Google Gemini API key (free tier available)

Tavily API key (free tier available)



---

Installation

Step 1: Clone Repository

git clone https://github.com/yourusername/market-anomaly-agent.git
cd market-anomaly-agent

Step 2: Create Virtual Environment

python -m venv .venv

Activate the virtual environment:

On Linux/Mac:

source .venv/bin/activate

On Windows:

.venv\Scripts\activate

Step 3: Install Dependencies

pip install -r requirements.txt


---

Configuration

Environment Variables

Create a .env file in the project root directory and add the following configuration:

# Required API Keys
GOOGLE_API_KEY=your_gemini_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

# LLM Configuration
LLM_MODEL=gemini-1.5-flash
LLM_TEMPERATURE=0.7

# Anomaly Detection Thresholds
ANOMALY_THRESHOLD=10.0
VOLUME_THRESHOLD=3.0
MAX_RETRIES=3

# Monitoring Settings
MONITORING_INTERVAL=300
MAX_ANOMALIES_PER_CYCLE=5
LOG_LEVEL=INFO

Obtaining API Keys

Google Gemini API Key:

1. Visit: https://aistudio.google.com/app/apikey


2. Click "Create API Key"


3. Copy the generated key and set it as GOOGLE_API_KEY in .env



Tavily API Key:

1. Visit: https://tavily.com


2. Sign up for a free account


3. Go to the API Keys section


4. Copy your key and set it as TAVILY_API_KEY in .env




---

Usage

All commands are run from the project root.

Single Monitoring Cycle

Run a one-off monitoring cycle for a custom watchlist:

python main.py --watchlist AAPL MSFT GOOGL

Continuous Monitoring

Enable continuous monitoring mode with a configurable interval (MONITORING_INTERVAL in seconds):

python main.py --watchlist AAPL TSLA MSFT GOOGL --continuous

Monitoring Indian Stocks

You can monitor NSE-listed Indian stocks via the .NS suffix:

python main.py --watchlist RELIANCE.NS TCS.NS INFY.NS HDFCBANK.NS


---

How It Works

1. Anomaly Detection

The system uses a multi-factor analysis to detect potential anomalies in each monitored stock.

Factors Evaluated:

Price change percentage

Example threshold: 10% move over a selected window


Volume spike ratio

Example threshold: 3× average volume


RSI (Relative Strength Index)

Identifies overbought/oversold conditions


Price volatility

Detects unusually large intraday or multi-day swings


Price gaps

Detects opening gaps up/down relative to previous close



Scoring System (0–9 Scale):

Each factor contributes points to an overall anomaly score:

Higher price/volume deviations → higher score

Confluence of multiple signals (e.g., price crash + volume spike + low RSI) → very high score


If the anomaly score ≥ 5, the system triggers a root cause investigation for that ticker.


---

2. Investigation Process

When an anomaly is detected, the system launches a LangGraph-powered investigation agent. The workflow:

1. Step 1 – Generate Search Queries

Multiple iterations of query refinement:

Chain-of-Thought reasoning

Expert role decomposition

Meta-prompt optimization




2. Step 2 – Execute Web Search (Tavily)

Queries are sent to Tavily API

Returns relevant news, filings, and commentary



3. Step 3 – Evaluate Evidence

Each result is scored on:

Source credibility

Relevance

Specificity




4. Step 4 – Determine Root Cause

Aggregates and synthesizes top evidence

Explains likely drivers behind the anomaly



5. Step 5 – Generate Report

Produces a structured markdown report with:

Summary

Root cause explanation

Evidence and links

Confidence and recommendations





Self-Correction Loop:

If the model’s confidence score < 70%, it:

Refines search queries

Runs additional Tavily calls

Retries up to MAX_RETRIES times (default: 3)




---

3. Query Generation Strategies

The agent uses three main iterations of query generation to maximize coverage and precision.

Iteration 1 – Chain-of-Thought

Step-by-step reasoning over the anomaly:

1. Assess severity of price move (magnitude, direction, speed)


2. Analyze volume pattern (spike, drying up, normal)


3. Consider common root causes:

Earnings

Guidance changes

M&A

Regulatory actions

Macro/sector news



4. Generate initial, targeted web search queries



Iteration 2 – Expert Role Prompts

The agent assumes multiple expert perspectives to diversify hypothesis space:

Earnings Analyst

Focus on: quarterly reports, guidance cuts/raises, analyst downgrades, earnings surprises


Legal Expert

Focus on: SEC filings, lawsuits, regulatory investigations, enforcement actions


Market Technician

Focus on: technical breakdowns, resistance/support levels, stop-loss cascades, short squeezes


Insider Tracker

Focus on: Form 4 insider trades, large block trades, insider selling/buying clusters



Each expert role proposes additional queries tailored to its domain.

Iteration 3 – Meta-Optimization

The LLM:

Reviews queries and search results generated so far

Identifies gaps (e.g., missing region, missing date filters, missing key terms)

Produces improved query variants to capture overlooked explanations




---

4. Evidence Evaluation

Each retrieved piece of evidence is scored along multiple dimensions.

Source Credibility Tiers

Tier 1 (1.00)

SEC.gov, official company investor relations pages


Tier 2 (0.90–0.94)

Bloomberg, Reuters, Wall Street Journal


Tier 3 (0.75–0.84)

CNBC, MarketWatch, Yahoo Finance


Tier 4 (0.60–0.68)

Seeking Alpha, Motley Fool


Tier 5 (0.30–0.40)

Twitter/X, Reddit, blogs, forums



Evaluation Metrics

Source credibility (weighted average)

Uses the above tiers to weight each source


Content relevance

How directly the article/post explains the specific anomaly


Information specificity

Concrete events (e.g., “Q3 earnings miss of 20%”) vs vague commentary


Overall confidence score (0–100%)

Combines credibility, relevance, and specificity



If confidence is low, the self-correction loop re-runs with refined queries.


---

5. Report Generation

All investigation results are written to the logs/ directory as markdown files.

Each report typically includes:

Anomaly Summary

Ticker symbol

Time of anomaly

Price change (absolute & percentage)

Volume details (absolute & multiple of average)


Investigation Status

Solved / Unsolved / Partially Explained


Confidence Score

0–100% confidence in the identified root cause


Root Cause Explanation

Narrative explanation of what likely happened and why


Evidence Quality Metrics

Number of sources

Weighted average credibility

Relevance and specificity summaries


Source Credibility Breakdown

How many Tier 1 / Tier 2 / ... sources contributed to the conclusion