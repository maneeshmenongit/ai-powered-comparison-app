# AI-Powered Weather Comparison Tool

## 🎯 What This Project Demonstrates

This is a multi-phase AI application that shows how LLMs can:
1. **Understand natural language** - Parse messy user queries into structured data
2. **Orchestrate API calls** - Make decisions about which services to query
3. **Provide intelligent analysis** - Compare results and make recommendations
4. **Handle real-world APIs** - With caching, error handling, and retry logic

**Example Query**: "Compare weather in New York for the next 5 days"

**What Happens**:
- ✅ AI extracts: location, days, weather providers
- ✅ Calls real weather APIs (Open-Meteo, WeatherAPI.com)
- ✅ AI analyzes results and provides meteorological insights
- ✅ Displays beautiful forecast comparison tables
- ✅ Caches results to reduce API costs

---

## 📁 Project Structure

```
ai-powered-comparison-app/
├── README.md              # This file
├── requirements.txt       # Python dependencies
├── .env                  # API keys (DO NOT COMMIT)
├── .gitignore           # Git ignore rules
├── main_phase2.py        # Phase 2 entry point ⭐ RUN THIS
├── docs/                # Documentation
│   ├── QUICK_START.md   # Setup guide
│   ├── SKILLS_ROADMAP.md # Learning curriculum
│   └── START_HERE.md    # Project overview
├── data/                # Data files
│   └── cache/           # API response cache
└── src/                 # Source code
    ├── phase1_poc.py    # Phase 1 - Mock data
    ├── phase2_main.py   # Phase 2 - Real APIs (deprecated, use ../main_phase2.py)
    ├── models/          # Data models
    │   └── weather.py   # WeatherForecast dataclass
    ├── api_clients/     # API client implementations
    │   ├── base_client.py        # Base with retry logic
    │   ├── openmeteo_client.py   # Open-Meteo (free, no key)
    │   └── weatherapi_client.py  # WeatherAPI.com (free tier)
    ├── llm/             # LLM-powered components
    │   ├── intent_parser.py      # Parse queries
    │   └── comparator.py         # Compare forecasts
    ├── services/        # Business logic
    │   └── cache_service.py      # File-based caching
    └── utils/           # Utilities
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.9 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### 2. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd ai-powered-comparison-app

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure API Key

```bash
# Copy the template
cp .env.template .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-proj-...
```

### 4. Run Phase 1 (Mock Data POC)

```bash
python src/phase1_poc.py
```

**Try these queries**:
- "Compare Uber and Lyft from Times Square to JFK Airport"
- "Which is cheaper from Manhattan to Brooklyn, Uber or Lyft?"

### 5. Run Phase 2 (Real Weather APIs) ⭐

```bash
python main_phase2.py
```

**Try these queries**:
- "Compare weather in New York for the next 5 days"
- "What's the weather forecast for London?"
- "Show me the weather in Tokyo for the next week"

---

## 🧠 How It Works (Technical Breakdown)

### **Component 1: Intent Parsing with LLM**

```python
def parse_user_query(query: str) -> Dict:
    """
    Converts natural language to structured data using OpenAI.
    
    Input: "Compare Uber and Lyft from Times Square to JFK"
    Output: {
        "origin": "Times Square, New York",
        "destination": "JFK Airport, New York",
        "services": ["uber", "lyft"]
    }
    """
```

**Why this matters**: Traditional programming requires exact formats (JSON, forms, etc.). 
AI lets users speak naturally while you get structured data for your code.

**Key learning**: 
- Using `response_format={"type": "json_object"}` ensures valid JSON
- `temperature=0` makes output deterministic for structured tasks
- System prompts guide the LLM's behavior

---

### **Component 2: API Client Layer**

```python
def get_uber_estimate(origin: str, destination: str) -> RideEstimate:
    """
    In POC: Returns mock data
    In production: Calls actual Uber API
    """
```

**Current State**: Using mock data to focus on AI logic
**Next Phase**: Replace with real API calls using `requests` library

**Why mock first**: 
- No need to sign up for API access yet
- Faster development and testing
- Learn AI concepts without API complexity

---

### **Component 3: AI-Powered Comparison**

```python
def compare_rides(estimates: List[RideEstimate]) -> str:
    """
    Uses LLM to analyze data and provide recommendations.
    
    This goes beyond simple min/max - it considers multiple factors
    and explains the reasoning in natural language.
    """
```

**Why use AI here**: Instead of hard-coded rules, the LLM can:
- Consider multiple factors (price, time, distance)
- Explain trade-offs in natural language
- Adapt to different user preferences later

---

## 📊 Data Flow Diagram

### Phase 1 (Mock Data)
```
User Query ("Compare Uber and Lyft...")
    ↓
[OpenAI: Parse Intent] → Structured JSON
    ↓
[Mock API Calls] → List of RideEstimates
    ↓
[OpenAI: Compare & Recommend] → Natural language analysis
    ↓
[Display Results] → Formatted table + recommendation
```

### Phase 2 (Real Weather APIs)
```
User Query ("Compare weather in New York...")
    ↓
[OpenAI: Parse Intent] → {location, days, providers}
    ↓
[Check Cache] → Cache hit? Return cached data
    ↓ (Cache miss)
[Call Weather APIs] → Open-Meteo + WeatherAPI.com
    ↓ (with retry logic)
[Normalize Data] → WeatherForecast objects
    ↓
[Cache Results] → Save to disk (60min TTL)
    ↓
[OpenAI: Compare Forecasts] → Natural language analysis
    ↓
[Display Results] → Formatted tables + AI insights
```

---

## 💰 Cost Estimation

Using **gpt-4o-mini** (cheapest model suitable for this):
- Input: ~$0.150 per 1M tokens
- Output: ~$0.600 per 1M tokens

**Per query cost**: ~$0.001 - $0.003 (less than a penny!)

**100 queries**: ~$0.10 - $0.30

This is why starting with AI for learning is so accessible.

---

## 🔄 Phase 1 vs Future Phases

### ✅ Phase 1 (Completed - POC)
- [x] Natural language query parsing
- [x] Mock API integration
- [x] AI-powered comparison
- [x] Beautiful CLI output

### ✅ Phase 2 (Completed - Real Weather APIs)
- [x] Pivoted from ride-sharing to weather APIs (due to Uber ToS restrictions)
- [x] Open-Meteo API integration (free, no key required)
- [x] WeatherAPI.com integration (free tier available)
- [x] BaseAPIClient with retry logic and exponential backoff
- [x] File-based caching system (60min TTL)
- [x] Data normalization across providers
- [x] WeatherForecast data models with dataclasses
- [x] AI-powered forecast comparison and analysis

### 🎯 Phase 3 (Web Interface)
- [ ] Streamlit web UI
- [ ] Session management
- [ ] Visual charts and graphs
- [ ] Save comparison history

### 🧠 Phase 4 (Intelligence)
- [ ] Remember user preferences
- [ ] Learn from past queries
- [ ] Personalized recommendations
- [ ] Multi-turn conversations

---

## 🐛 Troubleshooting

### "OpenAI API key not found"
- Check your `.env` file exists and has the key
- Make sure there are no quotes around the key
- Restart your terminal after setting environment variables

### "Module not found" errors
- Activate your virtual environment
- Run `pip install -r requirements.txt` again
- Verify Python version: `python --version` (should be 3.9+)

### API response errors
- Check your OpenAI account has credits
- Verify API key is valid at platform.openai.com
- Check your internet connection

---

## 📚 Learning Resources

### Understanding the Code
1. **OpenAI Chat Completions**: [Docs](https://platform.openai.com/docs/guides/chat-completions)
2. **JSON Mode**: [Docs](https://platform.openai.com/docs/guides/structured-outputs)
3. **Prompt Engineering**: [Guide](https://platform.openai.com/docs/guides/prompt-engineering)

### Python Libraries Used
- `openai`: Official OpenAI Python client
- `rich`: Beautiful terminal formatting
- `python-dotenv`: Environment variable management
- `dataclasses`: Clean data structures (Python standard library)

### Next Learning Steps
- **LangChain**: For more complex AI workflows
- **Pydantic**: For advanced data validation
- **FastAPI**: For building REST APIs
- **Streamlit**: For rapid web UI prototyping

---

## 🎓 Key Concepts You're Learning

### 1. **Prompt Engineering**
The art of instructing LLMs to get desired outputs:
- System prompts set behavior
- User prompts provide context
- Temperature controls randomness
- JSON mode ensures structured output

### 2. **LLM Function Calling**
Using AI to decide which functions to call with what parameters:
- Parse intent → determine which APIs to call
- Extract parameters → fill in API call arguments
- Format responses → present data clearly

### 3. **Agentic Patterns**
Building AI that can:
- Understand unstructured input
- Make decisions about actions
- Call external tools/APIs
- Synthesize results

### 4. **Data Engineering + AI**
Combining your DE skills with AI:
- ETL patterns for API data
- Data normalization across sources
- Validation and error handling
- Structured vs unstructured data

---

## 🚀 Next Steps After POC

1. **Get Real API Access**
   - Sign up for Uber Developer account
   - Get Lyft API credentials
   - Start with sandbox/test environments

2. **Enhance the Parsing**
   - Handle more complex queries
   - Support multiple destinations
   - Extract time preferences (now, tomorrow, etc.)

3. **Add More Services**
   - Food delivery (DoorDash, Uber Eats)
   - Hotels (Airbnb, Booking.com)
   - Flights (Kayak, Skyscanner APIs)

4. **Improve Intelligence**
   - Add context about traffic patterns
   - Consider weather conditions
   - Factor in user's past choices

5. **Build Production Features**
   - Error handling and retries
   - Logging and monitoring
   - API rate limiting
   - Response caching

---

## 💡 Questions to Think About

As you work through this POC, consider:

1. **When should you use AI vs traditional code?**
   - Parsing natural language → AI
   - Mathematical calculations → Traditional code
   - Pattern recognition → AI
   - Data validation → Mix of both

2. **How do you handle AI uncertainty?**
   - What if the LLM can't parse the query?
   - How do you validate AI-generated structured data?
   - When should you ask for clarification vs make assumptions?

3. **What's the trade-off between AI and code?**
   - AI: Flexible, handles edge cases, but costs money and is slower
   - Code: Fast, free, but rigid and requires handling every case

---

## 📝 Exercises to Try

1. **Modify the prompt**: Change the system prompt to extract additional fields like "time of day"

2. **Add a new service**: Create a mock function for a third service (e.g., "Via")

3. **Change the comparison logic**: Make the AI recommend based on different criteria (fastest vs cheapest)

4. **Handle errors**: What happens if the user enters gibberish? Add error handling.

5. **Add validation**: Use Pydantic models instead of raw dictionaries

---

## 🤝 Contributing Ideas

Once you're comfortable with this POC, try:
- Adding unit tests
- Creating a config file for different LLM models
- Implementing caching to save API costs
- Adding async support for parallel API calls

---

## 📄 License

This is a learning project - use it however you want!

---

## 🙋 Questions?

Remember: The best way to learn is by doing. Run the code, break it, fix it, and modify it!

Happy coding! 🚀
