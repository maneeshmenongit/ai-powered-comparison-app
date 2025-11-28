# 🚀 Quick Start Guide - Get Running in 15 Minutes

## Step-by-Step Setup

### Step 1: Set Up Python Environment (5 minutes)

```bash
# Create a project folder
mkdir comparison-app
cd comparison-app

# Create virtual environment
python -m venv venv

# Activate it
# On Mac/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# You should see (venv) in your terminal prompt now
```

---

### Step 2: Install Dependencies (2 minutes)

```bash
# Install required packages
pip install openai==1.12.0 python-dotenv==1.0.1 rich==13.7.0

# Verify installation
python -c "import openai; import rich; print('✓ All packages installed!')"
```

---

### Step 3: Get OpenAI API Key (5 minutes)

1. Go to https://platform.openai.com/api-keys
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key (starts with `sk-proj-...`)
5. **Important**: Save it somewhere - you can't see it again!

**Cost info**: This project will cost less than $1 for 100+ test queries

---

### Step 4: Configure Environment (2 minutes)

```bash
# Create .env file
touch .env

# Edit .env (use nano, vim, or any text editor)
# Add this line (replace with your actual key):
OPENAI_API_KEY=sk-proj-your-actual-key-here

# Save and close
```

**Important**: Never commit your .env file to git!

```bash
# Create .gitignore
echo ".env" > .gitignore
echo "venv/" >> .gitignore
echo "__pycache__/" >> .gitignore
```

---

### Step 5: Download & Run POC (1 minute)

Download `comparison_poc.py` from the files I've provided, then:

```bash
# Place comparison_poc.py in your comparison-app folder

# Run it!
python comparison_poc.py
```

**Expected output**:
```
🤖 AI-Powered Ride Comparison Tool (POC)

Enter your comparison query (or press Enter for example): 
Using example: Compare Uber and Lyft from Times Square to JFK Airport

Step 1: Parsing your query with AI...
✓ Parsed query successfully
  Origin: Times Square, New York
  Destination: JFK Airport, New York
  Services: uber, lyft

Step 2: Fetching ride estimates (using mock data)...
✓ Got 2 estimates

Step 3: Generating AI comparison...
✓ Analysis complete

[Beautiful table showing comparison]
[AI recommendation panel]
```

---

## Try These Queries

Once it's running, try:

1. **Default example** (just press Enter)
   - "Compare Uber and Lyft from Times Square to JFK Airport"

2. **Different locations**
   - "Which is cheaper from Manhattan to Brooklyn?"
   - "Compare rides from Central Park to LaGuardia"

3. **Implicit services** (doesn't specify Uber/Lyft)
   - "Get me from Grand Central to Newark Airport"
   - "I need a ride to JFK tomorrow"

4. **Test the AI parsing**
   - "What's the best way from my hotel to the airport?"
   - "Take me downtown from Times Square"

---

## Understanding the Output

### 1. **Query Parsing**
The AI extracted structured data from your natural language:
```
Origin: Times Square, New York
Destination: JFK Airport, New York  
Services: uber, lyft
```

### 2. **Comparison Table**
Shows side-by-side comparison of options:
- Price
- Duration
- Distance
- Vehicle type

### 3. **AI Recommendation**
Natural language explanation of which option is best and why.

---

## What's Happening Under the Hood

```python
# 1. Your query goes to OpenAI
"Compare Uber and Lyft from Times Square to JFK"

# 2. AI returns structured JSON
{
    "origin": "Times Square, New York",
    "destination": "JFK Airport, New York",
    "services": ["uber", "lyft"]
}

# 3. Mock API calls (simulating real APIs)
uber_estimate = get_uber_estimate(origin, destination)
lyft_estimate = get_lyft_estimate(origin, destination)

# 4. AI compares and recommends
comparison = compare_rides([uber_estimate, lyft_estimate])

# 5. Display results with Rich formatting
display_results(estimates, comparison)
```

---

## Common Issues & Solutions

### ❌ "OpenAI API key not found"
**Solution**: Check your .env file
```bash
# View your .env
cat .env

# Should see:
OPENAI_API_KEY=sk-proj-...

# If not, edit it:
nano .env
```

### ❌ "Module 'openai' not found"
**Solution**: Make sure virtual environment is activated
```bash
# You should see (venv) in your prompt
# If not:
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Then install again:
pip install -r requirements.txt
```

### ❌ "Rate limit exceeded"
**Solution**: Wait a minute, OpenAI has free tier limits
- Free tier: 3 requests per minute
- Paid tier: Much higher limits

### ❌ "Invalid API key"
**Solution**: Get a new key from platform.openai.com
- Keys can expire or be revoked
- Make sure you copied the entire key
- No spaces before or after the key

---

## Next Steps After POC Works

### 1. **Explore the Code** (30 minutes)
Open `comparison_poc.py` and read through:
- `parse_user_query()` - See how AI parsing works
- `compare_rides()` - See how AI analyzes data
- `display_results()` - See Rich formatting

### 2. **Make Simple Modifications** (1 hour)
Try changing:
```python
# In parse_user_query(), modify the system prompt:
system_prompt = """You are a helpful assistant that extracts ride comparison intent.
Extract: origin, destination, services, and TIME OF DAY.
..."""

# Add time_of_day to the returned JSON
```

### 3. **Add a Third Service** (1 hour)
```python
def get_via_estimate(origin: str, destination: str) -> RideEstimate:
    """Mock function for Via ride-sharing"""
    return RideEstimate(
        service="Via",
        price=38.00,
        duration_minutes=40,
        distance_miles=15.2,
        vehicle_type="Via Shared"
    )

# Add to main():
if "via" in [s.lower() for s in parsed.get("services", [])]:
    estimates.append(get_via_estimate(parsed["origin"], parsed["destination"]))
```

### 4. **Read the Documentation** (2-3 hours)
- `README.md` - Full project explanation
- `SKILLS_ROADMAP.md` - Learning path for all 4 phases

### 5. **Plan Your Next Phase** (1 hour)
Decide:
- Which real APIs to integrate first?
- Do you want to jump to web UI (Streamlit)?
- Or focus on making the AI smarter?

---

## Cost Tracking

Keep an eye on your OpenAI usage:
1. Go to https://platform.openai.com/usage
2. Check your daily spend
3. Set up billing alerts

**Expected costs for learning**:
- POC testing (50 queries): ~$0.10
- Phase 1 development: ~$0.50
- Phase 2 development: ~$2.00
- Phase 3 development: ~$3.00

**Total learning cost**: ~$5-10 for the entire project

---

## Learning Resources

### Must-Read (30 minutes each)
1. OpenAI Chat Completions: https://platform.openai.com/docs/guides/text-generation
2. JSON Mode: https://platform.openai.com/docs/guides/structured-outputs
3. Prompt Engineering Tips: https://platform.openai.com/docs/guides/prompt-engineering

### Watch Later (when integrating real APIs)
1. Uber API Docs: https://developer.uber.com/docs/riders/ride-requests/tutorials/api/introduction
2. Lyft API Docs: https://developer.lyft.com/docs/rides-api
3. LangChain Quickstart: https://python.langchain.com/docs/get_started/quickstart

---

## Getting Help

### If You're Stuck
1. **Check the error message** - Read it carefully
2. **Google the error** - Add "Python" to your search
3. **Check my documentation** - README.md might have the answer
4. **OpenAI Forums** - community.openai.com
5. **Stack Overflow** - tag: python, openai-api

### Questions to Ask Yourself
- Did I activate my virtual environment?
- Is my .env file in the right place?
- Did I copy my API key correctly?
- Am I in the right directory?

---

## Success Checklist ✅

Before moving to Phase 2, make sure you can:

- [ ] Run the POC without errors
- [ ] Get AI to parse different query formats
- [ ] See the comparison table display
- [ ] Understand what each function does
- [ ] Modify the mock data and see changes
- [ ] Explain how the AI parsing works
- [ ] Check your OpenAI usage dashboard

---

## What You've Learned 🎓

By running this POC, you now understand:

1. **How to call OpenAI API** from Python
2. **JSON mode** for structured outputs
3. **Prompt engineering** basics
4. **Data modeling** with dataclasses
5. **Environment variables** for secrets
6. **Terminal formatting** with Rich

These are the **foundational skills** for all AI agent projects!

---

## Ready for More?

Once this POC is running smoothly, read:
1. `SKILLS_ROADMAP.md` - See what skills you'll learn in Phase 2-4
2. `README.md` - Understand the architecture and design decisions

Then decide:
- Jump to Phase 2 (real APIs)?
- Or jump to Phase 3 (web UI)?
- Or work on another project from your document?

---

## 🎉 Congratulations!

You've taken the first step into AI agent development. This same pattern applies to:
- Your Zoom-to-JIRA agent
- MRR anomaly detection
- Tax filing agent
- Any other AI automation project

The hard part (understanding the concept) is done. Now it's just building! 🚀

---

## Remember

> "The best way to learn is by doing. Run the code, break it, fix it, modify it!"

Don't worry about making mistakes - that's how you learn. Have fun! 😊
