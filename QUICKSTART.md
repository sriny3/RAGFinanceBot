# Quick Start Guide: Frontend & Backend

**System**: RBAC-Enforced RAG Chatbot (Groq + SentenceTransformer)  
**Date**: March 26, 2026

---

## 🚀 Quick Start (2 Minutes)

### Option 1: Using Two Terminal Windows (Recommended)

#### Terminal 1: Start Backend
```bash
cd c:\development\CodeBasics\Bootcamp\Assignment\Assignment1\app\backend

python -m uvicorn main:app --reload
```

**Expected Output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### Terminal 2: Start Frontend
```bash
cd c:\development\CodeBasics\Bootcamp\Assignment\Assignment1\app\frontend-nextjs

npm run dev
```

**Expected Output:**
```
> next dev
  ▲ Next.js 14.0.0
  - Local:        http://localhost:3000
  - Environments: .env.local

 ✓ Ready in 2.3s
```

#### 3. Open Browser
```
http://localhost:3000
```

---

## ⚙️ Pre-Startup Checklist

### 1. Backend Already Has GROQ_API_KEY ✅
```bash
# Check .env file
cat app\backend\.env
```

**Current value:**
```
GROQ_API_KEY=gsk_your_groq_api_key_here
```

✅ **Already configured!**

### 2. Frontend Dependencies
```bash
# Navigate to frontend
cd app\frontend-nextjs

# Check if node_modules exists
dir node_modules

# If not, install dependencies
npm install

# Run dev server
npm run dev
```

### 3. Backend Dependencies (If Issues)
```bash
# Navigate to backend
cd app\backend

# Check Python version (must be 3.8+)
python --version

# Option A: Create fresh virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Option B: Use existing Python
# Install dependencies
pip install -r requirements.txt
```

---

## 📋 Full Setup Process

### Step 1: Setup Backend

```powershell
# Navigate to backend
cd c:\development\CodeBasics\Bootcamp\Assignment\Assignment1\app\backend

# Option A: Fresh environment (RECOMMENDED for clean state)
python -m venv venv
venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt

# Verify Python syntax (all files)
python -m py_compile main.py

# Start backend
python -m uvicorn main:app --reload
```

### Step 2: Setup Frontend (New Terminal)

```powershell
# Navigate to frontend
cd c:\development\CodeBasics\Bootcamp\Assignment\Assignment1\app\frontend-nextjs

# Install dependencies (if not already done)
npm install

# Start dev server
npm run dev
```

### Step 3: Open in Browser

```
http://localhost:3000
```

---

## 🔐 Login with Demo Users

### Available Demo Users

| Username | Password | Role | Access |
|----------|----------|------|--------|
| `emp_john` | `password123` | employee | general docs only |
| `fin_alice` | `password123` | finance | general + finance docs |
| `eng_bob` | `password123` | engineering | general + engineering docs |
| `mkt_sarah` | `password123` | marketing | general + marketing docs |
| `ceo_mary` | `password123` | c_level | **ALL docs** |

**Demo Login Steps:**
1. Go to http://localhost:3000
2. Click "Login"
3. Enter username (e.g., `emp_john`)
4. Enter password: `password123`
5. Click "Login"

**Admin Access:**
```
username: admin
password: admin123
```

---

## 📊 Infrastructure Configuration

| Service | Port | URL | Status |
|---------|------|-----|--------|
| Backend API | 8000 | http://localhost:8000 | ✅ POST /api/chat |
| Frontend | 3000 | http://localhost:3000 | ✅ GUI |
| Qdrant Cloud| 6333 | cloud.qdrant.io | ✅ Persistent Cloud |

---

## 🔍 Testing the System

### 1. Test Backend Health
```bash
# In any terminal/PowerShell
curl http://localhost:8000/api/health
```

**Expected Response:**
```json
{"status": "ok", "timestamp": "2026-03-26T..."}
```

### 2. Test Chat Endpoint
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "user_role": "finance",
    "query": "What is financial policy?"
  }'
```

**Expected Response:**
```json
{
  "answer": "The financial policy states...",
  "sources": ["chunk_001", "chunk_002"],
  "route": "finance",
  "flags": {"hallucination": false, "pii": false},
  "rbac_denied": false
}
```

### 3. Test Frontend
```
Open browser: http://localhost:3000
Login with: emp_john / password123
Chat about available documents
```

---

## ⚠️ Troubleshooting

### Backend Won't Start

#### Error: `ModuleNotFoundError: No module named 'pydantic_core'`

**Cause**: Pydantic dependency conflict (environment-specific issue)

**Solution Options:**

**Option 1: Fresh Virtual Environment (RECOMMENDED)**
```powershell
# Remove old env
Remove-Item -Recurse -Force venv

# Create fresh env
python -m venv venv

# Activate
venv\Scripts\activate

# Install
pip install -r requirements.txt

# Start
python -m uvicorn main:app --reload
```

**Option 2: Force Reinstall**
```powershell
pip install --force-reinstall --no-cache-dir -r requirements.txt
```

**Option 3: Use Python in Docker (If Local Issues Persist)**
```bash
# Install Docker
# Then run backend in container
docker build -t finbot-backend .
docker run -p 8000:8000 finbot-backend
```

---

#### Error: `GROQ_API_KEY not found`

**Solution**: Verify .env file
```powershell
# Check .env exists
dir .env

# Check content
type .env

# Should show: GROQ_API_KEY=gsk_...
```

If missing, add it:
```bash
# Get your Groq API key from: https://console.groq.com/keys
# Then edit .env and add:
GROQ_API_KEY=your_key_here
```

---

#### Error: `Port 8000 already in use`

**Solution**: Use different port or kill existing process
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID with actual number)
taskkill /PID 12345 /F

# Or start on different port
python -m uvicorn main:app --reload --port 8001
```

---

### Frontend Won't Start

#### Error: `npm: command not found`

**Solution**: Install Node.js
```
Download from: https://nodejs.org
Install Node.js (includes npm)
Restart terminal
Verify: npm --version
```

---

#### Error: `Port 3000 already in use`

**Solution**: Kill existing process
```powershell
# Find process using port 3000
netstat -ano | findstr :3000

# Kill process
taskkill /PID 12345 /F

# Or use different port
npm run dev -- --port 3001
```

---

#### Error: `Cannot find module 'next'`

**Solution**: Install dependencies
```bash
cd app\frontend-nextjs
npm install
npm run dev
```

---

### Services Won't Communicate

#### Symptom: Frontend shows "Connection refused" error

**Check:**
1. Backend running on port 8000? ✅
2. Frontend running on port 3000? ✅
3. CORS enabled in backend? ✅ (FastAPI automatically enables)

**Debug**:
```bash
# From frontend terminal, test backend
curl http://localhost:8000/api/health
```

Should return JSON response.

---

## 🎯 Startup Workflow

```
START HERE
    │
    ▼
┌─────────────────────┐
│ 1. Check Groq Key   │
│    (.env configured)│
└────────┬────────────┘
    YES │
    │
    ▼
┌─────────────────────┐
│ 2. Install Backend  │
│    pip install -r.. │
└────────┬────────────┘
    │
    ▼
┌─────────────────────┐
│ 3. Start Backend    │
│    Terminal 1       │
│    port 8000        │
└────────┬────────────┘
    │
    ▼
┌─────────────────────┐
│ 4. Install Frontend │
│    npm install      │
└────────┬────────────┘
    │
    ▼
┌─────────────────────┐
│ 5. Start Frontend   │
│    Terminal 2       │
│    port 3000        │
└────────┬────────────┘
    │
    ▼
┌─────────────────────┐
│ 6. Open Browser     │
│ localhost:3000      │
└────────┬────────────┘
    │
    ▼
┌─────────────────────┐
│ 7. Login & Chat!    │
│ emp_john / pwd123   │
└─────────────────────┘
```

---

## 📦 What Gets Started

### Backend (Port 8000)

**Services Started:**
- ✅ FastAPI server
- ✅ Document converter (Docling)
- ✅ Vector store (Qdrant) - in-memory mode
- ✅ Embeddings model (SentenceTransformer) - auto-downloaded on first use
- ✅ Groq LLM API client (uses external API)

**API Endpoints:**
- `POST /api/chat` — Chat with RBAC
- `GET /api/health` — Health check
- `GET /api/users/{username}` — User lookup
- `POST /admin/create-user` — Add user
- `POST /admin/ingest` — Upload documents

### Frontend (Port 3000)

**Next.js Components:**
- ✅ Login screen with demo users
- ✅ Chat interface (real-time messages)
- ✅ User profile display
- ✅ Document sources viewer
- ✅ Admin panel (user management)
- ✅ Safety flags display

---

## 🔄 Development Workflow

### Making Changes

#### Backend Code Changes
```
Edit: app/backend/pipeline/rag_pipeline.py
     ↓
[Uvicorn hot-reload active]
     ↓
Backend automatically restarts
     ↓
Test in browser/Postman
```

#### Frontend Code Changes
```
Edit: app/frontend-nextjs/components/ChatInterface.tsx
     ↓
[Next.js hot-reload active]
     ↓
Frontend automatically refreshes
     ↓
Test in browser
```

### No Manual Restart Needed

Both services have **hot-reload** enabled:
- **Backend**: `--reload` flag in uvicorn
- **Frontend**: Built-in Next.js dev server reload

Just save files and changes appear instantly!

---

## 📊 Performance Expectations

### First Run
- **Backend startup**: 3-5 seconds
- **SentenceTransformer download**: 1-2 minutes (first time only, ~500MB)
- **Frontend startup**: 5-10 seconds
- **First chat response**: 2-3 seconds (model needs to initialize)

### Subsequent Runs
- **Backend startup**: 2-3 seconds
- **Frontend startup**: 3-5 seconds  
- **Chat response**: 1-1.2 seconds ⚡

---

## 💡 Tips & Best Practices

### 1. Use Debug Mode
```bash
# Backend with verbose logging
DEBUG=True python -m uvicorn main:app --reload --log-level debug
```

### 2. Test with curl/Postman
```bash
# Health check
curl http://localhost:8000/api/health

# Chat request
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "u1", "user_role": "employee", "query": "test"}'
```

### 3. Watch Logs
Backend logs show:
- Received queries ✅
- RBAC decisions ✅
- Groq API calls ✅
- Error traceback ✅

### 4. Keep Both Terminals Open
Don't close either terminal while developing:
```
Terminal 1: Backend (port 8000)   [Keep Running]
Terminal 2: Frontend (port 3000)  [Keep Running]
Terminal 3: Testing/Git commands  [Optional]
```

# To reset vector store, delete:
# app/backend/qdrant_storage/
```

---

## 🎓 Next Steps After Startup

1. **Ingest Documents** (Admin Panel)
   - Navigate to http://localhost:3000/admin
   - Click "Ingest Document"
   - Upload PDF/DOCX/MD file
   - Select collection (general, finance, engineering, etc.)
   - Specify accessible roles

2. **Test RBAC**
   - Login as `emp_john` (employee)
   - Chat about available docs
   - Try asking about finance → "No access"
   - Login as `fin_alice` (finance)
   - Same question → See finance docs ✅

3. **Monitor System**
   - Check backend logs for errors
   - Watch RBAC decisions
   - Track embedding latency
   - Monitor token usage (Groq)

4. **Customize**
   - Edit roles in `config.py`
   - Adjust chunk size in `hierarchical_chunker.py`
   - Change embedding model in `vector_store.py`
   - Modify guardrails in `guardrails/`

---

## ✅ Verification Checklist

After startup, verify:

- [ ] Backend healthcheck: `curl http://localhost:8000/api/health`
- [ ] Frontend loads: `http://localhost:3000`
- [ ] Can login with demo user
- [ ] Chat endpoint responds
- [ ] RBAC filters work (test with different roles)
- [ ] Logs show no critical errors
- [ ] Both terminals show "Running"

---

## 📞 Support

**If Backend Won't Start:**
1. Check `.env` for GROQ_API_KEY
2. Try fresh `venv` (clean install)
3. Verify Python 3.8+
4. Check port 8000 not in use
5. View error logs carefully

**If Frontend Won't Start:**
1. Verify Node.js installed (`node --version`)
2. Try `npm install` again
3. Check port 3000 not in use
4. Clear `.next` cache: `rm -r .next`

**If Services Won't Communicate:**
1. Both running on correct ports?
2. Firewall blocking local traffic?
3. Check CORS headers in browser DevTools
4. Test endpoints with curl

---

**You're all set! 🚀 Happy chatting!**

Run the quick start commands above and your RBAC RAG chatbot will be live in minutes!
