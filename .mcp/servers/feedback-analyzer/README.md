# Feedback Analyzer MCP Server

Custom Model Context Protocol server providing AI-powered feedback analysis tools.

## Features

### Tools Available

1. **analyze_sentiment** - Analyze sentiment of single or batch feedback texts
   - Detects positive/negative/neutral sentiment
   - Provides confidence scores
   - Optional emotion detection

2. **calculate_nps** - Calculate Net Promoter Score from ratings
   - Accepts 0-10 scale ratings
   - Returns NPS score and breakdowns
   - Shows promoter/passive/detractor percentages

3. **identify_themes** - Extract key themes from feedback
   - Uses AI to identify common topics
   - Prioritizes themes by frequency and importance
   - Provides sentiment per theme

4. **detect_pain_points** - Identify customer issues
   - Detects problems and complaints
   - Severity classification
   - Actionable recommendations

5. **analyze_csv_file** - Analyze feedback CSV files
   - Reads and processes CSV data
   - Automatic NPS calculation if ratings present
   - Statistical summaries

6. **generate_summary** - Create executive summaries
   - Brief, detailed, or executive format options
   - Key findings and recommendations
   - Sentiment trends and metrics

## Usage with Docker AI

```bash
# Analyze sentiment
docker ai "Use feedback-analyzer to analyze sentiment of: 'Great product, very satisfied!'"

# Calculate NPS
docker ai "Calculate NPS from these ratings: 9, 10, 8, 7, 6, 9, 10"

# Identify themes from CSV
docker ai "Use feedback-analyzer to identify themes in data/samples/feedback.csv"

# Generate executive summary
docker ai "Generate an executive summary from the latest feedback data"
```

## Usage with MCP Gateway

Connect your AI client to `http://localhost:8080` and use the tools directly:

```
Analyze the sentiment of customer feedback in the last week
Calculate our current NPS score
What are the top 5 themes in recent feedback?
Identify critical pain points we need to address
```

## Environment Variables

- `OPENAI_API_KEY` - Required for AI-powered analysis
- `OPENAI_MODEL` - Optional, defaults to gpt-4o-mini

## Building the Server

```bash
cd .mcp/servers/feedback-analyzer
docker build -t customer-feedback/mcp-server .
```

## Running Standalone

```bash
docker run -it --rm \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -v $(pwd)/data:/data:ro \
  customer-feedback/mcp-server
```

## Development

To modify the server:

1. Edit [server.py](server.py)
2. Rebuild: `docker build -t customer-feedback/mcp-server .`
3. Restart: `docker-compose -f gordon-mcp.yml restart feedback-analyzer`

## Architecture

- **Framework**: MCP Python SDK
- **Transport**: stdio (standard input/output)
- **AI Provider**: OpenAI GPT-4o-mini
- **Data Processing**: pandas

## Adding New Tools

To add a new analysis tool:

1. Add tool definition in `list_tools()`
2. Implement `*_impl()` function
3. Add handler in `call_tool()`
4. Update this README

## Troubleshooting

### Server not responding
```bash
# Check logs
docker logs feedback-analyzer

# Restart
docker-compose -f gordon-mcp.yml restart feedback-analyzer
```

### OpenAI API errors
- Verify `OPENAI_API_KEY` is set
- Check API quota and billing
- Review rate limits

### CSV file not found
- Ensure file path is mounted in Docker volume
- Use absolute paths: `/workspace/data/file.csv`
