# Indus Flow — Deployment & Operations Guide
**Open Agent Hackathon 2026** | **Team Indus**

---

## 1. Quickstart (Local Development)

### Prerequisites
* Python 3.10+
* Git
* Docker & Docker Compose (Optional, for containerized run)

### Step-by-Step Local Setup
```bash
# 1. Navigate to project root
cd /Users/asiyaali/Downloads/indus-open-agent

# 2. Configure environment
cp .env.example .env

# 3. Run automated tests
python3 -m pytest -v tests/

# 4. Start the application
python3 -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```
Open your browser to:
* **Interactive Dashboard:** `http://127.0.0.1:8000/`
* **Swagger API Documentation:** `http://127.0.0.1:8000/docs`

---

## 2. Docker Container Deployment

The application includes a self-contained multi-stage `Dockerfile` and `docker-compose.yml`.

```bash
# Build and run with Docker Compose
docker-compose up --build -d

# Verify container health
docker-compose ps

# View live application logs
docker-compose logs -f
```

---

## 3. Environment Variables Reference

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `APP_ENV` | `development` | Runtime environment (`development` / `production`) |
| `APP_PORT` | `8000` | Port for FastAPI web server |
| `NVIDIA_API_KEY` | `mock-nvidia-key` | API key for NVIDIA NIM (`nvapi-...`). If empty/mock, uses structured emulator. |
| `NVIDIA_BASE_URL` | `https://integrate.api.nvidia.com/v1` | Endpoint for NVIDIA NIM inference |
| `NVIDIA_MODEL` | `meta/llama-3.1-70b-instruct` | Model identifier for reasoning |
| `METERLESS_API_KEY` | `mock-meterless-token` | API token for Meterless runtime |
| `METERLESS_ENGINE` | `world-model` | Meterless engine type |
| `METERLESS_ENDPOINT` | `https://api.meterless.ai/v1` | Endpoint for Meterless cloud API |
| `ZETARIS_HOST` | `localhost` | Zetaris Cloud Gateway host |
| `ZETARIS_PORT` | `10000` | Zetaris Lightning SQL PostgreSQL port |

---

## 4. Connecting Live Sponsor Services

### Connecting Live NVIDIA NIM
1. Obtain an API key from [build.nvidia.com](https://build.nvidia.com).
2. Set in `.env`:
   ```bash
   NVIDIA_API_KEY=nvapi-your-live-key-here
   ```
3. Restart the server. The header badge will automatically update to `Live NIM`.

### Connecting Live Meterless Engine
1. Obtain your API key from [meterless.ai](https://meterless.ai/engines.html).
2. Set in `.env`:
   ```bash
   METERLESS_API_KEY=your-meterless-token-here
   ```
3. The engine will connect to Meterless runtime.

### Connecting Live Zetaris Gateway
1. Run Zetaris Cloud Gateway locally via Docker:
   ```bash
   docker run -d -p 10000:10000 zetaris/gateway:latest
   ```
2. Update `.env` with host and credentials.
