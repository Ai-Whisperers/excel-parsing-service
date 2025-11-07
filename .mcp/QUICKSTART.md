# MCP Quick Start

Get started with MCP integration in 5 minutes.

## Prerequisites Check

- [ ] Docker Desktop installed and running
- [ ] OpenAI API key available
- [ ] `.env` file configured with `OPENAI_API_KEY`

## 30-Second Setup (Docker AI)

```bash
# 1. Start Docker Desktop (if not running)

# 2. Build custom analyzer
docker-compose -f gordon-mcp.yml build feedback-analyzer

# 3. Pull built-in servers
docker pull mcp/filesystem && docker pull mcp/fetch && docker pull mcp/time

# 4. Test it!
docker ai "List files in the data directory"
```

## 2-Minute Setup (MCP Gateway)

```bash
# 1. Build and start all services
docker-compose -f docker-compose.mcp-gateway.yml up -d --build

# 2. Verify running
docker-compose -f docker-compose.mcp-gateway.yml ps

# 3. Connect your AI client to http://localhost:8080
```

## Quick Test Commands

### Built-in Tools

```bash
# Filesystem
docker ai "What CSV files are in data/samples?"

# Fetch API
docker ai "Check health at http://localhost:10000/health"

# Time
docker ai "Current timestamp in ISO format"
```

### Custom Analyzer

```bash
# Sentiment Analysis
docker ai "Analyze sentiment: 'Amazing product, highly recommend!'"

# NPS Score
docker ai "Calculate NPS from ratings: 10, 9, 9, 8, 7, 6"

# CSV Analysis
docker ai "Analyze feedback in data/samples/feedback.csv"

# Theme Extraction
docker ai "Identify themes in recent customer feedback"
```

## Common Issues

### Docker not running
```bash
# Start Docker Desktop from Start menu or:
"C:\Program Files\Docker\Docker\Docker Desktop.exe"
```

### Build fails
```bash
# Clean rebuild
docker-compose -f gordon-mcp.yml build feedback-analyzer --no-cache
```

### OpenAI errors
```bash
# Check your .env file
grep OPENAI_API_KEY .env

# Should show: OPENAI_API_KEY=sk-...
```

### Gateway won't start
```bash
# View detailed logs
docker-compose -f docker-compose.mcp-gateway.yml logs

# Restart fresh
docker-compose -f docker-compose.mcp-gateway.yml down
docker-compose -f docker-compose.mcp-gateway.yml up -d --build
```

## Next Steps

- **Full Setup Guide**: [SETUP.md](SETUP.md)
- **MCP Overview**: [README.md](README.md)
- **Custom Server Details**: [servers/feedback-analyzer/README.md](servers/feedback-analyzer/README.md)

## Tool Summary

| Tool | Purpose | Example |
|------|---------|---------|
| **filesystem** | Read project files | "Show contents of config.py" |
| **fetch** | HTTP requests | "Test API health endpoint" |
| **time** | Timestamps | "Current date and time" |
| **analyze_sentiment** | Sentiment analysis | "Analyze: 'Great service!'" |
| **calculate_nps** | NPS scoring | "NPS from [9,10,8,7,6]" |
| **identify_themes** | Topic extraction | "Find themes in feedback.csv" |
| **detect_pain_points** | Issue detection | "Find customer pain points" |
| **analyze_csv_file** | CSV insights | "Analyze feedback.csv" |
| **generate_summary** | Executive summary | "Summarize recent feedback" |