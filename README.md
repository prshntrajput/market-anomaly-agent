# Market Anomaly Detection Agent

An AI-powered agent that monitors stock markets in real-time, detects anomalies, investigates root causes using web search, and generates detailed reports.

## Overview

This system continuously monitors stock prices, detects significant market anomalies (price drops, volume spikes), and automatically investigates the root cause using LangGraph agents, web search, and LLM-powered analysis.

## Features

- Real-time market monitoring for multiple stocks
- Multi-factor anomaly detection (price change, volume spike, RSI, volatility, gaps)
- AI-powered root cause investigation with self-correction loops
- Advanced query generation using Chain-of-Thought reasoning and expert role prompts
- Evidence evaluation with source credibility scoring
- Professional markdown report generation
- Continuous monitoring mode with configurable intervals

## System Architecture

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
+---------------------------+
| Query Generator |
| - Chain-of-Thought |
| - Expert Role Prompts |
| - Meta-optimization |
+---------------------------+
     |
     v
Web Search (Tavily API)
     |
     v
Evidence Evaluator
     |
     v
Report Generator (Markdown)


## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Google Gemini API key (free tier available)
- Tavily API key (free tier available)

## Installation

### Step 1: Clone Repository

git clone https://github.com/yourusername/market-anomaly-agent.git
cd market-anomaly-agent


### Step 2: Create Virtual Environment

python -m venv .venv

Activate virtual environment
On Linux/Mac:
source .venv/bin/activate

On Windows:
.venv\Scripts\activate


### Step 3: Install Dependencies
pip install -r requirements.txt


## Configuration

### Create Environment File

Create a `.env` file in the project root directory:

Required API Keys
GOOGLE_API_KEY=your_gemini_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

LLM Configuration
LLM_MODEL=gemini-1.5-flash
LLM_TEMPERATURE=0.7

Anomaly Detection Thresholds
ANOMALY_THRESHOLD=10.0
VOLUME_THRESHOLD=3.0
MAX_RETRIES=3

Monitoring Settings
MONITORING_INTERVAL=300
MAX_ANOMALIES_PER_CYCLE=5
LOG_LEVEL=INFO


### Obtaining API Keys

**Google Gemini API Key:**
1. Visit https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the generated key

**Tavily API Key:**
1. Visit https://tavily.com
2. Sign up for a free account
3. Navigate to the API Keys section
4. Copy your API key

## Usage

### Basic Commands

**Single monitoring cycle:**
python main.py --watchlist AAPL MSFT GOOGL


**Continuous monitoring:**
python main.py --watchlist AAPL TSLA MSFT GOOGL --continuous


**Monitor Indian stocks:**
python main.py --watchlist RELIANCE.NS TCS.NS INFY.NS HDFCBANK.NS


## How It Works

### 1. Anomaly Detection

The system monitors stocks using multi-factor analysis:

**Factors Evaluated:**
- Price change percentage (threshold: 10%)
- Volume spike ratio (threshold: 3x)
- RSI (Relative Strength Index)
- Price volatility
- Price gaps

**Scoring System:**
Each factor contributes points to an anomaly score (0-9 scale). A score of 5 or higher triggers an investigation.

### 2. Investigation Process

When an anomaly is detected, the agent follows this workflow:

Step 1: Generate Search Queries
|
+-- Iteration 1: Chain-of-Thought reasoning
+-- Iteration 2: Expert role prompts
+-- Iteration 3: Meta-prompt optimization
|
v
Step 2: Execute Web Search (Tavily)
|
v
Step 3: Evaluate Evidence
|
+-- Source credibility scoring
+-- Content relevance analysis
+-- Specificity assessment
|
v
Step 4: Determine Root Cause
|
v
Step 5: Generate Report

The process includes a self-correction loop. If confidence is below 70%, the agent refines queries and retries (up to 3 attempts).

### 3. Query Generation Strategies

**Iteration 1 - Chain-of-Thought:**
Analyze step-by-step:

Assess severity of price drop

Analyze volume pattern

Identify likely root causes

Generate targeted queries

**Iteration 2 - Expert Role Prompts:**Four expert perspectives:

Earnings Analyst: Focus on quarterly reports

Legal Expert: Focus on SEC filings and lawsuits

Market Technician: Focus on trading patterns

Insider Tracker: Focus on Form 4 filings

**Iteration 3 - Meta-optimization:**
LLM critiques previous queries and suggests improvements


### 4. Evidence Evaluation

**Source Credibility Tiers:**
- Tier 1 (1.00): SEC.gov, company investor relations
- Tier 2 (0.90-0.94): Bloomberg, Reuters, WSJ
- Tier 3 (0.75-0.84): CNBC, MarketWatch, Yahoo Finance
- Tier 4 (0.60-0.68): Seeking Alpha, Motley Fool
- Tier 5 (0.30-0.40): Twitter, Reddit, blogs

**Evaluation Metrics:**
- Overall source credibility (weighted average)
- Content relevance to anomaly
- Information specificity
- Confidence score (0-100%)

### 5. Report Generation

Reports are saved in the `logs/` directory as markdown files.

**Report Contents:**
- Anomaly summary (ticker, price change, volume)
- Investigation status (solved/unsolved)
- Confidence score
- Root cause explanation
- Evidence quality metrics
- Source credibility breakdown
- Recommendations


