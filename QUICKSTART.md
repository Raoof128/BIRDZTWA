# 🚀 Quick Start Guide

Get Browser Isolation running in 5 minutes!

## Option 1: Docker (Recommended)

```bash
# Clone or navigate to project
cd browser_isolation

# Start full stack
docker-compose up -d

# Access services
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Dashboard: localhost:8501
```

## Option 2: Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Run API server
python api/server.py

# In another terminal, run dashboard
streamlit run client/safe_viewer.py
```

## Option 3: CLI Tool

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Render a URL
python cli/isolationctl.py render https://example.com

# Check URL policy
python cli/isolationctl.py check-url https://github.com

# Generate report
python cli/isolationctl.py report --output audit.md

# View statistics
python cli/isolationctl.py stats
```

## First Test

Try isolating a safe URL:

```bash
python cli/isolationctl.py render https://example.com --report example_report.md
```

Expected output:
- ✅ Policy check passed
- ✅ Fetched successfully
- ✅ Sanitization complete
- Risk score: 0-2/10 (minimal risk)

## Test with Dangerous Page

```bash
python cli/isolationctl.py render file://$(pwd)/examples/dangerous_page.html
```

Expected output:
- 🚨 Multiple scripts removed
- 🚨 Event handlers stripped
- 🚨 Dangerous URLs blocked
- Risk score: 7-9/10 (high risk)

## API Example

```bash
# Check health
curl http://localhost:8000/api/v1/health

# Render a URL
curl -X POST http://localhost:8000/api/v1/render \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

## Dashboard Usage

1. Open localhost:8501
2. Enter URL in sidebar
3. Click "Isolate & Render"
4. View safe content in main area
5. Check "Blocked Items" tab for threats
6. Generate report with button

## Common Issues

### Playwright not installed
```bash
playwright install chromium
```

If your host is missing OS-level libraries for Chromium, install the packages recommended in the [Playwright Linux prerequisites](https://playwright.dev/docs/browsers#linux).

### Port already in use
```bash
# API (change port)
python api/server.py --port 8001

# Dashboard
streamlit run client/safe_viewer.py --server.port 8502
```

### Permission errors (Docker)
```bash
# Fix volume permissions
sudo chown -R $USER:$USER logs/ reports/
```

## Next Steps

- Read full [README.md](README.md)
- Review [config/block_rules.yaml](config/block_rules.yaml)
- Run tests: `pytest tests/ -v`
- Try dangerous example: [examples/dangerous_page.html](examples/dangerous_page.html)

## Need Help?

Check the full documentation in README.md or API docs at `/docs`

