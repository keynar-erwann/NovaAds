# 🔮 Nova Ads: AI-Driven Graphic Designer & Ad Strategist

Nova Ads is a sophisticated AI-powered web application designed to automate the process of market research and advertisement creation. It features an AI Agent called "Nova" that assists users by researching their product niche, analyzing market trends, and generating high-converting ad posters.



## Features

*   **Intelligent Agentic Workflow:** Nova isn't just a chatbot; she's an agent capable of using a suite of tools (Web Search, Market Analysis, Content Extraction) to make informed design decisions.
*   **Automated Market Research:** Integrated with Serper and Tavily to gather real-time data on products, trends, and competitors in specific countries and languages.
*   **AI Image Generation:** Uses Google's Gemini-3.1-flash-image models to generate professional advertisement posters based on strategic analysis.
*   **SQL Session Management:** Implements a robust SQL-based repository (SQLite) to store message history and maintain session state across user interactions.




## 🛠️ Tech Stack

*   **Frontend:** JavaScript, HTML, CSS.
*   **Backend:** Python (FastAPI).
*   **Database:** SQL (SQLite) for history and memory management.
*   **AI Models:** 
    *   **Logic:** Gemini-2.5-flash
    *   **Image generation:** Gemini-3.1-flash-image-preview
**APIs:** Tavily (Web Search & Extraction), Serper (Google Search).



## Project Structure


├── app.py              # Main FastAPI Backend & AI Agent logic
├── requirements.txt    # Backend dependencies
├── README.md           # Project documentation
└── UI/                 # Frontend assets
    ├── index.html      # Landing page
    ├── styles.css      # Custom UI styling
    └── script.js       # Frontend logic & API interaction


Note: The database (`memory.db`) and the `generated_ads/` folder are created automatically in the root directory when the application is first run.



## Setup & Installation

### 1. Prerequisites
Ensure you have **Python 3.10+** installed on your system.

### 2. Installation
Clone the repository and install the required Python libraries:
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory and add your API keys:

GOOGLE_API_KEY=your_gemini_key
TAVILY_API_KEY=your_tavily_key
SERPERDEV_API_KEY=your_serper_key



### 4. Running the App
Start the FastAPI server:

python app.py

The application will be accessible at `http://localhost:8000`.



## Nova
When you submit a request, Nova follows a structured advertising pipeline:
1.  **Market Research:** Uses `market_research` and `web_search` to understand your niche.
2.  **Strategic Analysis:** Processes extracted data to find the best angle for your ad.
3.  **Creative Design:** Crafts a detailed prompt and generates the ad poster using the `generate_image` tool.
