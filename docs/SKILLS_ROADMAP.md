# Python & AI Skills Roadmap for Comparison App

## 📋 Overview

This document maps out exactly what Python and AI skills you need for each phase of the project. 
Since you're already a data engineer with Python experience, I'll note which skills you likely 
already have and which are new.

---

## Phase 1: Foundation (Weeks 1-2)

### Skills You Likely Already Have ✅

#### 1. **Python Fundamentals**
```python
# You already know these from data engineering:
- Variables, data types, functions
- Lists, dictionaries, sets
- Loops and conditionals
- File I/O and path handling
- Virtual environments
- pip and package management
```

#### 2. **Data Structures**
```python
# Familiar territory for a DE:
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class RideEstimate:
    service: str
    price: float
    duration_minutes: int
```
**Why it matters here**: Clean data models for API responses

#### 3. **Environment Variables**
```python
# You've probably used these in DE work:
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
```
**Why it matters here**: Securely storing API keys

#### 4. **JSON Handling**
```python
# Standard DE skill:
import json

data = json.loads(response_text)
output = json.dumps(data, indent=2)
```
**Why it matters here**: All API communication uses JSON

---

### New Skills to Learn 🆕

#### 1. **OpenAI API Basics**
**Difficulty**: Easy | **Time**: 1-2 hours

```python
from openai import OpenAI

client = OpenAI(api_key="your-key")

# Basic completion
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ]
)

# Extract the response
answer = response.choices[0].message.content
```

**Key concepts to understand**:
- **Messages array**: Conversation history format
- **Roles**: system (instructions), user (queries), assistant (responses)
- **Model selection**: Different models for different use cases
- **Temperature**: Controls randomness (0 = deterministic, 1 = creative)

**Resources**:
- Official quickstart: https://platform.openai.com/docs/quickstart
- Pricing: https://openai.com/api/pricing/

**Practice exercise**:
Write a script that asks OpenAI to explain a Python concept and prints the response.

---

#### 2. **Structured Output with JSON Mode**
**Difficulty**: Easy | **Time**: 1 hour

```python
# Force the LLM to return valid JSON
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "Return data as JSON with fields: name, age, city"},
        {"role": "user", "content": "Tell me about John who is 30 from NYC"}
    ],
    response_format={"type": "json_object"}  # KEY: Forces JSON output
)

data = json.loads(response.choices[0].message.content)
print(data["name"])  # Guaranteed to have these fields
```

**Why this is powerful**: 
- No more parsing messy text responses
- Direct integration with your Python code
- Reliable data extraction from natural language

**Practice exercise**:
Create a function that takes a movie description and returns JSON with: title, year, genre, rating

---

#### 3. **Prompt Engineering Fundamentals**
**Difficulty**: Medium | **Time**: 2-3 hours

**System Prompts** - Set behavior and constraints:
```python
system_prompt = """You are a travel assistant that extracts location data.
Rules:
1. Always include city and state/country
2. Convert airport codes to full names (e.g., JFK → JFK Airport, New York)
3. If location is ambiguous, default to the most famous one
4. Return JSON with: origin, destination

Be precise and consistent."""
```

**User Prompts** - Provide context and query:
```python
user_prompt = "I need to go from LAX to Times Square next Tuesday"
```

**Key principles**:
1. **Be specific**: "Extract location" vs "Extract origin and destination as JSON"
2. **Give examples**: Few-shot prompting improves accuracy
3. **Set constraints**: "Maximum 50 words" or "Only include X, Y, Z fields"
4. **Handle edge cases**: Tell it what to do when unclear

**Common patterns**:
```python
# Pattern 1: Extraction
"Extract {fields} from this text: {text}. Return as JSON."

# Pattern 2: Classification  
"Is this query about: A) rides, B) food, C) hotels? Return only the letter."

# Pattern 3: Transformation
"Convert this natural language to SQL: {query}"
```

**Practice exercise**:
Write prompts for:
1. Extracting restaurant info from reviews
2. Classifying customer support tickets by urgency
3. Converting addresses to standardized format

**Resources**:
- OpenAI Prompt Engineering Guide: https://platform.openai.com/docs/guides/prompt-engineering
- Learn Prompting Course: https://learnprompting.org/

---

#### 4. **API Error Handling**
**Difficulty**: Easy | **Time**: 1 hour

```python
from openai import OpenAI, OpenAIError
import time

def call_openai_with_retry(prompt: str, max_retries: int = 3):
    """
    Robust API calling with error handling.
    As a DE, you know why this matters!
    """
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                timeout=30  # Don't wait forever
            )
            return response.choices[0].message.content
            
        except OpenAIError as e:
            if "rate_limit" in str(e).lower():
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"API Error: {e}")
                if attempt == max_retries - 1:
                    raise
                    
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise
    
    return None
```

**Why this matters**:
- API calls can fail (network issues, rate limits, etc.)
- OpenAI has rate limits based on your tier
- Costs money - don't want to waste retries

**DE connection**: This is like handling failed SQL queries or API timeouts in data pipelines

---

#### 5. **Rich Terminal Output** (Nice to have)
**Difficulty**: Very Easy | **Time**: 30 minutes

```python
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

# Colored output
console.print("[green]Success![/green]")
console.print("[red]Error occurred[/red]")

# Tables
table = Table(title="Ride Comparison")
table.add_column("Service", style="cyan")
table.add_column("Price", style="green")
table.add_row("Uber", "$45.50")
table.add_row("Lyft", "$42.00")
console.print(table)

# Panels for emphasis
console.print(Panel("Important message", title="Alert", border_style="red"))
```

**Why include this**: 
- Makes your CLI tool look professional
- Easier to debug with color-coded output
- Users will appreciate clear formatting

**Resources**: https://rich.readthedocs.io/

---

### Phase 1 Learning Path 🛤️

**Week 1: OpenAI Fundamentals**
- Day 1-2: Set up OpenAI account, API key, run first completion
- Day 3-4: Practice prompt engineering with different tasks
- Day 5: Learn JSON mode and structured outputs
- Weekend: Build simple extraction tool (practice project)

**Week 2: Build the POC**
- Day 1-2: Implement intent parser
- Day 3: Create mock API functions
- Day 4: Add comparison logic
- Day 5: Polish with Rich formatting
- Weekend: Test, refine, document

**Estimated time commitment**: 10-15 hours total

---

## Phase 2: Add Intelligence (Weeks 3-4)

### Skills You'll Need 🆕

#### 1. **LangChain Basics**
**Difficulty**: Medium | **Time**: 3-4 hours

LangChain is a framework that makes building AI applications easier. It handles common patterns 
like chaining prompts, managing conversation history, and integrating tools.

```python
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

# Define your output structure with Pydantic
class LocationExtraction(BaseModel):
    origin: str = Field(description="Starting location")
    destination: str = Field(description="Ending location")
    services: list[str] = Field(description="Services to compare")

# Create parser
parser = PydanticOutputParser(pydantic_object=LocationExtraction)

# Create prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "Extract location data from user query. {format_instructions}"),
    ("user", "{query}")
])

# Create chain
llm = ChatOpenAI(model="gpt-4o-mini")
chain = prompt | llm | parser

# Use it
result = chain.invoke({
    "query": "Compare Uber and Lyft from NYC to Boston",
    "format_instructions": parser.get_format_instructions()
})

print(result.origin)  # Type-safe! Your IDE knows the structure
```

**Why LangChain**:
- Eliminates boilerplate code
- Built-in retry logic and error handling
- Easy to chain multiple LLM calls
- Great for complex workflows

**Key concepts**:
- **Chains**: Sequence of operations (prompt → LLM → parser)
- **Templates**: Reusable prompts with variables
- **Output Parsers**: Convert LLM text to Python objects
- **LCEL** (LangChain Expression Language): The `|` operator for chaining

**Practice exercise**:
Convert your Phase 1 POC to use LangChain instead of raw OpenAI calls

**Resources**:
- LangChain Quickstart: https://python.langchain.com/docs/get_started/quickstart
- LCEL Guide: https://python.langchain.com/docs/expression_language/

---

#### 2. **Pydantic for Data Validation**
**Difficulty**: Easy | **Time**: 2 hours

```python
from pydantic import BaseModel, Field, validator
from typing import Optional

class RideEstimate(BaseModel):
    """
    Pydantic ensures data integrity - critical for DE work!
    """
    service: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)  # Must be > 0
    duration_minutes: int = Field(..., ge=1)
    distance_miles: float = Field(..., gt=0)
    vehicle_type: str
    surge_multiplier: Optional[float] = 1.0
    
    @validator('service')
    def service_must_be_lowercase(cls, v):
        return v.lower()
    
    @validator('price')
    def price_reasonable(cls, v):
        if v > 1000:
            raise ValueError('Price seems unreasonably high')
        return v
    
    class Config:
        # Validate on assignment
        validate_assignment = True

# Usage
try:
    ride = RideEstimate(
        service="Uber",
        price=45.50,
        duration_minutes=30,
        distance_miles=15.2,
        vehicle_type="UberX"
    )
    print(ride.model_dump_json())  # Convert to JSON
except ValidationError as e:
    print(e.errors())
```

**Why this matters**:
- Catch bad data before it causes issues
- Self-documenting code (the model IS the documentation)
- Easy serialization to/from JSON
- Type hints for IDE autocomplete

**DE connection**: Like schema validation in data pipelines, but at runtime

**Practice exercise**:
Create Pydantic models for:
1. API request parameters
2. API response data  
3. User preferences

---

#### 3. **Real API Integration**
**Difficulty**: Medium | **Time**: 4-5 hours

```python
import requests
from typing import Dict, Any

class UberClient:
    """
    Real API client structure.
    Pattern you'll use for all services.
    """
    
    BASE_URL = "https://api.uber.com/v1.2"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
    
    def get_price_estimate(
        self, 
        start_lat: float, 
        start_lng: float,
        end_lat: float, 
        end_lng: float
    ) -> Dict[str, Any]:
        """Get price estimate between two points"""
        
        endpoint = f"{self.BASE_URL}/estimates/price"
        params = {
            "start_latitude": start_lat,
            "start_longitude": start_lng,
            "end_latitude": end_lat,
            "end_longitude": end_lng
        }
        
        try:
            response = self.session.get(endpoint, params=params, timeout=10)
            response.raise_for_status()  # Raise exception for 4xx/5xx
            return response.json()
        
        except requests.exceptions.Timeout:
            raise APIError("Uber API timeout")
        except requests.exceptions.HTTPError as e:
            raise APIError(f"Uber API error: {e}")
        except Exception as e:
            raise APIError(f"Unexpected error: {e}")
    
    def geocode_address(self, address: str) -> tuple[float, float]:
        """
        Convert address to coordinates.
        You'll need this to translate AI-parsed locations to API format.
        """
        # Use Google Maps Geocoding API or similar
        pass

# Usage
client = UberClient(api_key=os.getenv("UBER_API_KEY"))
try:
    estimate = client.get_price_estimate(
        start_lat=40.7580,  # Times Square
        start_lng=-73.9855,
        end_lat=40.6413,  # JFK
        end_lng=-73.7781
    )
    print(estimate)
except APIError as e:
    print(f"Failed to get estimate: {e}")
```

**Key challenges**:
1. **Authentication**: Each API has different auth (API keys, OAuth, tokens)
2. **Rate limiting**: Most APIs limit requests per minute/day
3. **Data normalization**: Each API returns different JSON structures
4. **Geocoding**: Converting "Times Square" to lat/lng coordinates
5. **Error codes**: Handling specific API error responses

**Pattern to follow**:
1. Create a client class for each service
2. Use a common interface (same method names)
3. Handle errors consistently
4. Add retry logic for transient failures
5. Cache results to avoid duplicate calls

**Practice exercise**:
1. Sign up for one free API (e.g., OpenWeatherMap)
2. Build a client class
3. Handle at least 3 different error types
4. Add request caching

---

#### 4. **Data Normalization**
**Difficulty**: Easy (for you as a DE!) | **Time**: 2 hours

```python
from typing import Protocol
from datetime import datetime

# Define common interface
class RideServiceProtocol(Protocol):
    """All ride services must implement this interface"""
    def get_estimate(self, origin: str, destination: str) -> RideEstimate:
        ...

class UberAdapter:
    """Adapter pattern to normalize Uber API responses"""
    
    def normalize_response(self, uber_data: Dict) -> RideEstimate:
        """
        Convert Uber's JSON structure to our standard format.
        
        Uber returns:
        {
            "prices": [{
                "display_name": "UberX",
                "estimate": "$30-40",
                "duration": 2100,  # seconds
                "distance": 15.2  # miles
            }]
        }
        
        We want:
        RideEstimate with consistent field names and types
        """
        
        price_data = uber_data["prices"][0]
        
        # Parse price range to get average
        price_str = price_data["estimate"].replace("$", "")
        low, high = map(float, price_str.split("-"))
        avg_price = (low + high) / 2
        
        return RideEstimate(
            service="uber",
            price=avg_price,
            duration_minutes=price_data["duration"] // 60,
            distance_miles=price_data["distance"],
            vehicle_type=price_data["display_name"]
        )

class LyftAdapter:
    """Same pattern for Lyft"""
    
    def normalize_response(self, lyft_data: Dict) -> RideEstimate:
        # Lyft has different JSON structure - normalize it here
        pass
```

**Why this matters**:
- Each API returns different structures
- Your comparison logic needs consistent data
- Makes adding new services easy (just create new adapter)

**DE connection**: This is ETL! Extract (API call) → Transform (normalize) → Load (your app)

---

#### 5. **Caching for API Efficiency**
**Difficulty**: Easy | **Time**: 1-2 hours

```python
from functools import lru_cache
import hashlib
import json
from datetime import datetime, timedelta

class APICache:
    """
    Simple caching to avoid repeated API calls.
    Important for:
    1. Reducing costs
    2. Respecting rate limits
    3. Faster responses
    """
    
    def __init__(self, ttl_seconds: int = 300):  # 5 min default
        self.cache: Dict[str, tuple[Any, datetime]] = {}
        self.ttl = timedelta(seconds=ttl_seconds)
    
    def get_cache_key(self, *args, **kwargs) -> str:
        """Create unique key from function arguments"""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.ttl:
                return value
            else:
                del self.cache[key]  # Expired
        return None
    
    def set(self, key: str, value: Any):
        """Store value with current timestamp"""
        self.cache[key] = (value, datetime.now())

# Usage with your API client
cache = APICache(ttl_seconds=300)

def get_ride_estimate_cached(origin: str, destination: str, service: str):
    """Cached version of API call"""
    
    cache_key = cache.get_cache_key(origin, destination, service)
    
    # Try cache first
    cached = cache.get(cache_key)
    if cached:
        print(f"Cache hit for {service}")
        return cached
    
    # Cache miss - make real API call
    print(f"Cache miss for {service} - calling API")
    result = call_real_api(origin, destination, service)
    
    # Store in cache
    cache.set(cache_key, result)
    return result
```

**Advanced: Redis cache for production**:
```python
import redis
import pickle

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cached_api_call(key: str, api_func, ttl: int = 300):
    """Use Redis for persistent, shared cache"""
    
    cached = redis_client.get(key)
    if cached:
        return pickle.loads(cached)
    
    result = api_func()
    redis_client.setex(key, ttl, pickle.dumps(result))
    return result
```

**Why this matters**:
- Same query within 5 minutes? Use cached data
- Reduces API costs significantly
- Respects rate limits
- Much faster for repeated queries

**DE connection**: Like caching query results in data pipelines

---

### Phase 2 Learning Path 🛤️

**Week 3: Framework & Real APIs**
- Day 1-2: Learn LangChain basics, convert POC
- Day 3-4: Sign up for APIs, build client classes
- Day 5: Implement data normalization
- Weekend: Add caching and error handling

**Week 4: Integration & Testing**
- Day 1-2: Integrate 3-4 real APIs
- Day 3: Handle edge cases (timeouts, invalid data)
- Day 4-5: Testing and refinement
- Weekend: Documentation and code cleanup

**Estimated time commitment**: 15-20 hours total

---

## Phase 3: Web Interface (Weeks 5-6)

### Skills You'll Need 🆕

#### 1. **Streamlit Basics**
**Difficulty**: Very Easy | **Time**: 2-3 hours

Streamlit makes web apps ridiculously simple. Perfect for data engineers who want UI without learning React!

```python
import streamlit as st

# Title
st.title("🚗 Ride Comparison Tool")

# Text input
query = st.text_input("Where do you want to go?", 
                     placeholder="Compare Uber and Lyft from Times Square to JFK")

# Button
if st.button("Compare Rides"):
    with st.spinner("Analyzing options..."):
        # Your existing code here
        result = compare_rides(query)
        
        # Display results
        st.success("Found the best options!")
        
        # Create columns for comparison
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Uber", "$45.50", delta="-$2.50")
        
        with col2:
            st.metric("Lyft", "$42.00", delta="3 min faster")
        
        # Chart
        st.bar_chart({"Uber": [45.50], "Lyft": [42.00]})

# Sidebar for settings
with st.sidebar:
    st.header("Preferences")
    prefer_speed = st.checkbox("Prioritize speed over price")
    max_price = st.slider("Max price", 0, 100, 50)
```

**Why Streamlit**:
- Zero HTML/CSS/JavaScript knowledge needed
- Live reload during development
- Built-in components for charts, tables, maps
- Session state management included
- Deploy easily to Streamlit Cloud (free)

**Key concepts**:
- **Reactive**: Page reruns on interaction
- **Session state**: Persist data between reruns
- **Caching**: Use `@st.cache_data` for expensive operations
- **Layout**: columns, expanders, tabs, sidebar

**Practice exercise**:
Convert your CLI tool to a simple Streamlit app with:
1. Text input for query
2. Button to trigger comparison
3. Table showing results

**Resources**:
- Streamlit Docs: https://docs.streamlit.io/
- Gallery (examples): https://streamlit.io/gallery

---

#### 2. **Session State Management**
**Difficulty**: Easy | **Time**: 1-2 hours

```python
import streamlit as st

# Initialize session state
if 'search_history' not in st.session_state:
    st.session_state.search_history = []

if 'user_preferences' not in st.session_state:
    st.session_state.user_preferences = {
        'prefer_speed': False,
        'max_price': 100
    }

# Get user query
query = st.text_input("Your query")

if st.button("Search"):
    # Add to history
    st.session_state.search_history.append({
        'query': query,
        'timestamp': datetime.now(),
        'results': compare_rides(query)
    })
    
    # Display results
    st.write(st.session_state.search_history[-1]['results'])

# Show history in sidebar
with st.sidebar:
    st.header("Recent Searches")
    for i, search in enumerate(reversed(st.session_state.search_history[-5:])):
        if st.button(f"{search['query'][:30]}...", key=f"history_{i}"):
            # Re-run that search
            st.write(search['results'])
```

**Why this matters**:
- Remember user's searches across page refreshes
- Show search history
- Maintain user preferences
- Enable multi-step workflows

---

#### 3. **Visualizations with Plotly**
**Difficulty**: Easy | **Time**: 2 hours

```python
import plotly.graph_objects as go
import streamlit as st

def create_comparison_chart(estimates: List[RideEstimate]):
    """Create interactive comparison chart"""
    
    fig = go.Figure()
    
    # Add bars for each service
    services = [e.service for e in estimates]
    prices = [e.price for e in estimates]
    durations = [e.duration_minutes for e in estimates]
    
    # Price bars
    fig.add_trace(go.Bar(
        name='Price',
        x=services,
        y=prices,
        marker_color='lightblue',
        text=[f'${p:.2f}' for p in prices],
        textposition='auto',
    ))
    
    # Duration bars (on secondary axis)
    fig.add_trace(go.Bar(
        name='Duration',
        x=services,
        y=durations,
        marker_color='lightgreen',
        text=[f'{d} min' for d in durations],
        textposition='auto',
        yaxis='y2'
    ))
    
    # Layout
    fig.update_layout(
        title='Price & Duration Comparison',
        xaxis_title='Service',
        yaxis_title='Price ($)',
        yaxis2=dict(
            title='Duration (min)',
            overlaying='y',
            side='right'
        ),
        barmode='group'
    )
    
    return fig

# In your Streamlit app
st.plotly_chart(create_comparison_chart(results), use_container_width=True)
```

**Chart types you'll use**:
- Bar charts: Price comparisons
- Line charts: Price trends over time
- Scatter plots: Price vs. duration
- Maps: Show routes (using Plotly Mapbox)

---

#### 4. **Async Operations** (Advanced)
**Difficulty**: Medium | **Time**: 3-4 hours

For calling multiple APIs simultaneously:

```python
import asyncio
import aiohttp
from typing import List

async def fetch_uber_async(session, origin, destination):
    """Async API call to Uber"""
    async with session.get(uber_url, params=params) as response:
        return await response.json()

async def fetch_lyft_async(session, origin, destination):
    """Async API call to Lyft"""
    async with session.get(lyft_url, params=params) as response:
        return await response.json()

async def get_all_estimates(origin: str, destination: str) -> List[RideEstimate]:
    """
    Fetch all estimates in parallel instead of sequential.
    
    Sequential: Uber (2s) + Lyft (2s) + DoorDash (2s) = 6s total
    Parallel:   max(2s, 2s, 2s) = 2s total
    """
    async with aiohttp.ClientSession() as session:
        # Launch all requests simultaneously
        tasks = [
            fetch_uber_async(session, origin, destination),
            fetch_lyft_async(session, origin, destination),
            fetch_doordash_async(session, origin, destination)
        ]
        
        # Wait for all to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        estimates = []
        for result in results:
            if not isinstance(result, Exception):
                estimates.append(normalize_response(result))
        
        return estimates

# Use in Streamlit
estimates = asyncio.run(get_all_estimates(origin, destination))
```

**Why async**:
- 3x faster when calling 3 APIs
- Better user experience
- More efficient use of resources

**When not to use**:
- Single API calls (no benefit)
- CPU-bound tasks (use multiprocessing instead)
- When APIs have strict rate limits

---

### Phase 3 Learning Path 🛤️

**Week 5: Basic Web UI**
- Day 1-2: Learn Streamlit basics, convert CLI to web
- Day 3: Add session state and history
- Day 4: Implement basic charts
- Day 5: Polish styling and layout
- Weekend: User testing and feedback

**Week 6: Advanced Features**
- Day 1-2: Add async API calls
- Day 3: Implement advanced visualizations
- Day 4: Add export functionality (CSV, PDF reports)
- Day 5: Deploy to Streamlit Cloud
- Weekend: Documentation and demo

**Estimated time commitment**: 15-20 hours total

---

## Phase 4: Intelligence & Personalization (Weeks 7-8)

### Skills You'll Need 🆕

#### 1. **Conversation Memory with LangChain**
**Difficulty**: Medium | **Time**: 3-4 hours

```python
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain_openai import ChatOpenAI

# Initialize memory
memory = ConversationBufferMemory()

# Create conversation chain
llm = ChatOpenAI(model="gpt-4o-mini")
conversation = ConversationChain(
    llm=llm,
    memory=memory,
    verbose=True
)

# Multi-turn conversation
response1 = conversation.predict(input="I need a ride to JFK tomorrow morning")
# AI remembers: User wants JFK, tomorrow morning

response2 = conversation.predict(input="Actually, make it from Brooklyn")
# AI knows: From Brooklyn to JFK, tomorrow morning

response3 = conversation.predict(input="What was my destination again?")
# AI responds: "JFK Airport" (from memory)
```

**Memory types**:
- **ConversationBufferMemory**: Keep all messages (simple, but grows)
- **ConversationSummaryMemory**: Summarize old messages (saves tokens)
- **ConversationBufferWindowMemory**: Keep only last N messages
- **ConversationEntityMemory**: Track entities (names, places, etc.)

**Why this matters**:
- Natural follow-up questions
- Users don't repeat themselves
- Better UX with context awareness

---

#### 2. **User Preferences with SQLite**
**Difficulty**: Easy (you know SQL!) | **Time**: 2-3 hours

```python
import sqlite3
from datetime import datetime

class UserPreferences:
    """Track user preferences to personalize recommendations"""
    
    def __init__(self, db_path: str = "user_data.db"):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()
    
    def create_tables(self):
        """Create schema for preferences"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                user_id TEXT PRIMARY KEY,
                prefer_speed BOOLEAN,
                max_price REAL,
                favorite_service TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                query TEXT,
                selected_service TEXT,
                price_paid REAL,
                timestamp TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES preferences(user_id)
            )
        """)
        self.conn.commit()
    
    def learn_from_selection(self, user_id: str, service: str, price: float):
        """Update preferences based on user's actual choice"""
        
        # Record the choice
        self.conn.execute("""
            INSERT INTO search_history (user_id, selected_service, price_paid, timestamp)
            VALUES (?, ?, ?, ?)
        """, (user_id, service, price, datetime.now()))
        
        # Analyze patterns
        cursor = self.conn.execute("""
            SELECT 
                AVG(price_paid) as avg_price,
                MODE(selected_service) as favorite_service,
                COUNT(*) as total_searches
            FROM search_history
            WHERE user_id = ?
            GROUP BY user_id
        """, (user_id,))
        
        result = cursor.fetchone()
        if result:
            avg_price, favorite_service, _ = result
            
            # Update preferences
            self.conn.execute("""
                UPDATE preferences
                SET favorite_service = ?,
                    max_price = ?,
                    updated_at = ?
                WHERE user_id = ?
            """, (favorite_service, avg_price * 1.2, datetime.now(), user_id))
        
        self.conn.commit()
    
    def get_personalized_recommendation(self, user_id: str, estimates: List[RideEstimate]):
        """Use learned preferences to recommend best option"""
        
        cursor = self.conn.execute("""
            SELECT prefer_speed, max_price, favorite_service
            FROM preferences
            WHERE user_id = ?
        """, (user_id,))
        
        prefs = cursor.fetchone()
        if not prefs:
            return min(estimates, key=lambda e: e.price)  # Default: cheapest
        
        prefer_speed, max_price, favorite_service = prefs
        
        # Filter by max price
        affordable = [e for e in estimates if e.price <= max_price]
        if not affordable:
            affordable = estimates  # Relax constraint if nothing matches
        
        # Score each option based on preferences
        def score_option(estimate: RideEstimate) -> float:
            score = 0
            
            # Prefer favorite service
            if estimate.service == favorite_service:
                score += 10
            
            # Prefer speed or price based on preference
            if prefer_speed:
                score += (60 - estimate.duration_minutes)  # Lower duration = higher score
            else:
                score += (100 - estimate.price)  # Lower price = higher score
            
            return score
        
        return max(affordable, key=score_option)
```

**Why track preferences**:
- Learn what users actually choose (not just what they say)
- Personalized recommendations
- Identify patterns (always picks fastest, etc.)

**DE connection**: This is just analytics! User behavior tracking and analysis

---

#### 3. **LLM-Based Recommendation Logic**
**Difficulty**: Medium | **Time**: 3-4 hours

```python
def generate_smart_recommendation(
    estimates: List[RideEstimate],
    user_context: Dict,
    search_history: List[Dict]
) -> str:
    """
    Use LLM to make intelligent recommendations considering:
    - Current options
    - User's past behavior  
    - Context (time of day, weather, etc.)
    """
    
    # Build rich context for the LLM
    context = f"""
User Context:
- Time: {datetime.now().strftime('%A, %I:%M %p')}
- Past preferences: {analyze_past_choices(search_history)}
- Stated priorities: {"speed" if user_context.get('prefer_speed') else "price"}

Available Options:
{format_estimates_for_llm(estimates)}

Recent Patterns:
{analyze_recent_patterns(search_history)}

Task: Recommend the best option and explain why, considering their past behavior and current context.
Be specific about trade-offs.
"""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a personalized travel assistant."},
            {"role": "user", "content": context}
        ],
        temperature=0.7
    )
    
    return response.choices[0].message.content

def analyze_past_choices(history: List[Dict]) -> str:
    """Summarize user's typical behavior"""
    if not history:
        return "No past data"
    
    services = [h['selected_service'] for h in history]
    prices = [h['price_paid'] for h in history]
    
    return f"""
- Usually chooses: {max(set(services), key=services.count)}
- Average spend: ${sum(prices)/len(prices):.2f}
- Total trips: {len(history)}
"""
```

**Why use LLM for recommendations**:
- Can consider nuanced factors
- Explains reasoning in natural language
- Adapts to complex preferences
- Handles edge cases gracefully

---

#### 4. **A/B Testing Framework** (Advanced)
**Difficulty**: Medium | **Time**: 4-5 hours

```python
import random
from enum import Enum

class RecommendationStrategy(Enum):
    RULE_BASED = "rule_based"
    LLM_BASED = "llm_based"
    HYBRID = "hybrid"

class ABTesting:
    """Test which recommendation strategy works best"""
    
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.create_ab_tables()
    
    def create_ab_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ab_tests (
                test_id TEXT PRIMARY KEY,
                user_id TEXT,
                strategy TEXT,
                recommended_service TEXT,
                user_selected_service TEXT,
                accepted_recommendation BOOLEAN,
                timestamp TIMESTAMP
            )
        """)
        self.conn.commit()
    
    def assign_strategy(self, user_id: str) -> RecommendationStrategy:
        """Randomly assign user to A or B group"""
        strategies = list(RecommendationStrategy)
        return random.choice(strategies)
    
    def log_result(self, test_id: str, user_id: str, 
                   strategy: RecommendationStrategy,
                   recommended: str, actual_selection: str):
        """Track if user accepted our recommendation"""
        
        accepted = (recommended == actual_selection)
        
        self.conn.execute("""
            INSERT INTO ab_tests VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (test_id, user_id, strategy.value, recommended, 
              actual_selection, accepted, datetime.now()))
        self.conn.commit()
    
    def analyze_results(self) -> Dict:
        """Which strategy performs better?"""
        
        cursor = self.conn.execute("""
            SELECT 
                strategy,
                COUNT(*) as total_recommendations,
                SUM(CASE WHEN accepted_recommendation THEN 1 ELSE 0 END) as accepted,
                AVG(CASE WHEN accepted_recommendation THEN 1.0 ELSE 0.0 END) as acceptance_rate
            FROM ab_tests
            GROUP BY strategy
        """)
        
        results = {}
        for row in cursor:
            strategy, total, accepted, rate = row
            results[strategy] = {
                'total': total,
                'accepted': accepted,
                'acceptance_rate': rate
            }
        
        return results
```

**Why A/B test**:
- Data-driven decisions
- Validate if AI recommendations actually help users
- Continuous improvement
- Understand what works

**DE connection**: This is just experimentation analysis!

---

### Phase 4 Learning Path 🛤️

**Week 7: Memory & Personalization**
- Day 1-2: Implement conversation memory
- Day 3: Add user preferences database
- Day 4-5: Build learning from behavior
- Weekend: Test personalization logic

**Week 8: Advanced Intelligence**
- Day 1-2: Implement LLM-based recommendations
- Day 3: Set up A/B testing
- Day 4: Analyze results and refine
- Day 5: Polish and optimize
- Weekend: Comprehensive testing and documentation

**Estimated time commitment**: 20-25 hours total

---

## Summary: Total Learning Path

### Time Investment by Phase
- **Phase 1**: 10-15 hours (Foundation)
- **Phase 2**: 15-20 hours (Intelligence)  
- **Phase 3**: 15-20 hours (Web UI)
- **Phase 4**: 20-25 hours (Personalization)

**Total**: 60-80 hours over 8 weeks = ~10 hours/week

---

## Skills Dependency Map

```
Python Fundamentals (you have) ✅
    ↓
OpenAI API Basics → JSON Mode → Prompt Engineering
    ↓
LangChain Basics → Chains → Memory
    ↓
Real API Integration → Data Normalization → Caching
    ↓
Streamlit Basics → Session State → Visualizations
    ↓
User Preferences DB → Learning from Behavior → A/B Testing
    ↓
Production Ready App 🎉
```

---

## Resources by Phase

### Phase 1
- OpenAI Cookbook: https://cookbook.openai.com/
- Prompt Engineering Guide: https://learnprompting.org/
- Rich Documentation: https://rich.readthedocs.io/

### Phase 2
- LangChain Docs: https://python.langchain.com/
- Pydantic Tutorial: https://docs.pydantic.dev/
- Requests Library: https://requests.readthedocs.io/

### Phase 3
- Streamlit Gallery: https://streamlit.io/gallery
- Plotly Examples: https://plotly.com/python/
- Async Python: https://realpython.com/async-io-python/

### Phase 4
- LangChain Memory: https://python.langchain.com/docs/modules/memory/
- SQLite Tutorial: https://www.sqlitetutorial.net/
- A/B Testing Guide: https://www.optimizely.com/optimization-glossary/ab-testing/

---

## Next Steps

1. **Set up your environment** (Day 1)
   - Install Python 3.9+
   - Create virtual environment
   - Install requirements.txt
   - Get OpenAI API key

2. **Run the POC** (Day 1-2)
   - Execute comparison_poc.py
   - Experiment with different queries
   - Understand the code flow

3. **Modify the POC** (Day 3-5)
   - Add a new mock service
   - Change the comparison logic
   - Enhance the output format

4. **Plan Phase 2** (Day 6-7)
   - Research APIs you want to integrate
   - Sign up for developer accounts
   - Read API documentation

5. **Keep learning!**
   - One concept at a time
   - Practice with small examples
   - Build incrementally

---

## 💪 You've Got This!

As a data engineer, you already have the hardest skills:
- ✅ Python proficiency
- ✅ Data modeling & validation
- ✅ API integration patterns
- ✅ SQL and database design
- ✅ ETL and data pipelines

You're just learning to add **AI orchestration** to your toolkit!

The skills you're learning here apply to ALL three projects in your document:
- Zoom-to-JIRA agent
- MRR anomaly detection
- Tax filing agent

Master this comparison tool, and the others will be much easier. 🚀
