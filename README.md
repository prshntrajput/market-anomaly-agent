
# Market Anomaly Detection Agent

An AI-powered agent that monitors stock markets in real-time, detects anomalies, investigates root causes using web search, and generates detailed reports.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Step 1: Clone Repository](#step-1-clone-repository)
  - [Step 2: Create Virtual Environment](#step-2-create-virtual-environment)
  - [Step 3: Install Dependencies](#step-3-install-dependencies)
- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
  - [Obtaining API Keys](#obtaining-api-keys)
- [Usage](#usage)
  - [Single Monitoring Cycle](#single-monitoring-cycle)
  - [Continuous Monitoring](#continuous-monitoring)
  - [Monitoring Indian Stocks](#monitoring-indian-stocks)
- [How It Works](#how-it-works)
  - [1. Anomaly Detection](#1-anomaly-detection)
  - [2. Investigation Process](#2-investigation-process)
  - [3. Query Generation Strategies](#3-query-generation-strategies)
  - [4. Evidence Evaluation](#4-evidence-evaluation)
  - [5. Report Generation](#5-report-generation)

---

## Overview

This system continuously monitors stock prices, detects significant market anomalies (price drops, volume spikes, etc.), and automatically investigates the root cause using LangGraph agents, web search, and LLM-powered analysis. It then generates detailed professional markdown reports summarizing findings, evidence, and recommendations.

---

## Features

- ✅ Real-time market monitoring for multiple stocks  
- ✅ Multi-factor anomaly detection  
  - Price change percentage  
  - Volume spike ratio  
  - RSI (Relative Strength Index)  
  - Volatility  
  - Price gaps  
- ✅ AI-powered root cause investigation with self-correction loops  
- ✅ Advanced query generation using:  
  - Chain-of-Thought reasoning  
  - Expert role prompts  
  - Meta-optimization  
- ✅ Evidence evaluation with source credibility scoring  
- ✅ Professional markdown report generation  
- ✅ Continuous monitoring mode with configurable time intervals  

---

## System Architecture

```text
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

## Prerequisites

Python 3.10 or higher

pip (Python package manager)

Google Gemini API key (free tier available)

Tavily API key (free tier available)



---

## Installation

Step 1: Clone Repository

git clone https://github.com/yourusername/market-anomaly-agent.git
cd market-anomaly-agent


---

Step 2: Create Virtual Environment

python -m venv .venv

Activate the virtual environment:

On Linux/Mac:

source .venv/bin/activate

On Windows:

.venv\Scripts\activate


---

Step 3: Install Dependencies

pip install -r requirements.txt


---

## Configuration

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


---

## Obtaining API Keys

Google Gemini API Key

1. Visit: https://aistudio.google.com/app/apikey


2. Click Create API Key


3. Copy the generated key


4. Paste it into your .env file as GOOGLE_API_KEY




---

## Tavily API Key

1. Visit: https://tavily.com


2. Sign up for a free account


3. Navigate to the API Keys section


4. Copy your key


5. Paste it into your .env file as TAVILY_API_KEY




---

## Usage

All commands must be executed from the project root directory.


---

Single Monitoring Cycle

python main.py --watchlist AAPL MSFT GOOGL


---

Continuous Monitoring

python main.py --watchlist AAPL TSLA MSFT GOOGL --continuous


---

Monitoring Indian Stocks

python main.py --watchlist RELIANCE.NS TCS.NS INFY.NS HDFCBANK.NS


---

## How It Works


---

1. Anomaly Detection

The system uses a multi-factor analysis to detect potential anomalies in each monitored stock.

Factors Evaluated:

Price change percentage

Volume spike ratio

RSI (Relative Strength Index)

Price volatility

Price gaps


Scoring System (0–9 Scale):

Each factor contributes points to the anomaly score.
If the anomaly score ≥ 5, an investigation is triggered.


---

2. Investigation Process

Once an anomaly is detected, the system launches a LangGraph-powered investigation agent.

Workflow:

1. Generate search queries


2. Execute web search via Tavily


3. Evaluate evidence


4. Determine root cause


5. Generate markdown report



## Self-Correction Loop:

If confidence falls below 70%, the agent refines queries and retries up to MAX_RETRIES.


---

3. Query Generation Strategies

Iteration 1 – Chain-of-Thought

Assess severity of price movement

Analyze volume behavior

Identify potential root causes

Generate targeted queries



---

Iteration 2 – Expert Role Prompts

Expert perspectives used:

Earnings Analyst – Earnings, guidance, revenue

Legal Expert – SEC filings, lawsuits

Market Technician – Technical analysis, chart patterns

Insider Tracker – Insider trades, Form 4 filings



---

Iteration 3 – Meta-Optimization

The LLM critiques prior queries and generates optimized improvements.


---

4. Evidence Evaluation

Source Credibility Tiers:

Tier 1 (1.00) – SEC.gov, company IR

Tier 2 (0.90–0.94) – Bloomberg, Reuters, WSJ

Tier 3 (0.75–0.84) – CNBC, MarketWatch, Yahoo Finance

Tier 4 (0.60–0.68) – Seeking Alpha, Motley Fool

Tier 5 (0.30–0.40) – Twitter, Reddit, blogs


## Evaluation Metrics:

Weighted average source credibility

Content relevance

Information specificity

Final confidence score (0–100%)



---

5. Report Generation

All details are saved in the logs/ directory as markdown files.

Each report includes:

Anomaly summary

Investigation status

Confidence score

Root cause explanation

Evidence quality metrics

Source credibility breakdown

Final recommendation