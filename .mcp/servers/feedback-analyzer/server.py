#!/usr/bin/env python3
"""
Custom MCP Server for Customer Feedback Analysis
Provides AI-powered feedback analysis tools via Model Context Protocol
"""

import os
import sys
import json
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

# Add the API directory to path to import project modules
sys.path.insert(0, '/app/api')

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Initialize MCP Server
app = Server("feedback-analyzer")

# Import OpenAI for analysis
try:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    HAS_OPENAI = True
except Exception as e:
    print(f"Warning: OpenAI not available: {e}", file=sys.stderr)
    HAS_OPENAI = False

# Import pandas for data processing
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List all available feedback analysis tools"""
    tools = [
        Tool(
            name="analyze_sentiment",
            description="Analyze sentiment of feedback text or batch of feedback entries",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Single feedback text to analyze"
                    },
                    "texts": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Batch of feedback texts to analyze"
                    },
                    "include_emotions": {
                        "type": "boolean",
                        "description": "Whether to include emotion detection",
                        "default": False
                    }
                },
                "oneOf": [
                    {"required": ["text"]},
                    {"required": ["texts"]}
                ]
            }
        ),
        Tool(
            name="calculate_nps",
            description="Calculate Net Promoter Score from rating responses (0-10 scale)",
            inputSchema={
                "type": "object",
                "properties": {
                    "ratings": {
                        "type": "array",
                        "items": {"type": "number", "minimum": 0, "maximum": 10},
                        "description": "List of NPS ratings (0-10)"
                    }
                },
                "required": ["ratings"]
            }
        ),
        Tool(
            name="identify_themes",
            description="Extract key themes and topics from feedback using AI",
            inputSchema={
                "type": "object",
                "properties": {
                    "feedbacks": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of feedback texts to analyze"
                    },
                    "max_themes": {
                        "type": "number",
                        "description": "Maximum number of themes to extract",
                        "default": 5
                    }
                },
                "required": ["feedbacks"]
            }
        ),
        Tool(
            name="detect_pain_points",
            description="Identify customer pain points and issues from feedback",
            inputSchema={
                "type": "object",
                "properties": {
                    "feedbacks": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of feedback texts to analyze"
                    },
                    "severity_threshold": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Minimum severity level to report",
                        "default": "medium"
                    }
                },
                "required": ["feedbacks"]
            }
        ),
        Tool(
            name="analyze_csv_file",
            description="Analyze a feedback CSV file and generate insights",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to CSV file containing feedback data"
                    },
                    "text_column": {
                        "type": "string",
                        "description": "Name of column containing feedback text",
                        "default": "feedback"
                    },
                    "rating_column": {
                        "type": "string",
                        "description": "Name of column containing ratings (optional)"
                    }
                },
                "required": ["file_path", "text_column"]
            }
        ),
        Tool(
            name="generate_summary",
            description="Generate executive summary from feedback analysis results",
            inputSchema={
                "type": "object",
                "properties": {
                    "feedbacks": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of feedback texts"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["brief", "detailed", "executive"],
                        "description": "Summary format style",
                        "default": "brief"
                    }
                },
                "required": ["feedbacks"]
            }
        )
    ]
    return tools


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle tool calls"""
    try:
        if name == "analyze_sentiment":
            result = await analyze_sentiment_impl(arguments)
        elif name == "calculate_nps":
            result = await calculate_nps_impl(arguments)
        elif name == "identify_themes":
            result = await identify_themes_impl(arguments)
        elif name == "detect_pain_points":
            result = await detect_pain_points_impl(arguments)
        elif name == "analyze_csv_file":
            result = await analyze_csv_file_impl(arguments)
        elif name == "generate_summary":
            result = await generate_summary_impl(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, indent=2)
        )]


async def analyze_sentiment_impl(args: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze sentiment of feedback text(s)"""
    if not HAS_OPENAI:
        return {"error": "OpenAI API not configured"}

    texts = args.get("texts", [args.get("text")] if args.get("text") else [])
    include_emotions = args.get("include_emotions", False)

    if not texts:
        return {"error": "No text provided"}

    results = []
    for text in texts:
        prompt = f"""Analyze the sentiment of this customer feedback.

Feedback: {text}

Provide:
1. Overall sentiment (positive/negative/neutral)
2. Sentiment score (-1.0 to 1.0)
3. Confidence level (0.0 to 1.0)
{"4. Detected emotions (joy, anger, sadness, etc.)" if include_emotions else ""}

Respond in JSON format."""

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )

        analysis = json.loads(response.choices[0].message.content)
        results.append({
            "text": text[:100] + "..." if len(text) > 100 else text,
            "analysis": analysis
        })

    return {
        "results": results,
        "count": len(results),
        "timestamp": datetime.now().isoformat()
    }


async def calculate_nps_impl(args: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate Net Promoter Score"""
    ratings = args.get("ratings", [])

    if not ratings:
        return {"error": "No ratings provided"}

    # Validate ratings
    if not all(0 <= r <= 10 for r in ratings):
        return {"error": "All ratings must be between 0 and 10"}

    # Calculate NPS
    promoters = sum(1 for r in ratings if r >= 9)
    detractors = sum(1 for r in ratings if r <= 6)
    passives = sum(1 for r in ratings if 7 <= r <= 8)
    total = len(ratings)

    nps = ((promoters - detractors) / total * 100) if total > 0 else 0

    return {
        "nps_score": round(nps, 2),
        "promoters": promoters,
        "promoters_pct": round(promoters / total * 100, 2),
        "passives": passives,
        "passives_pct": round(passives / total * 100, 2),
        "detractors": detractors,
        "detractors_pct": round(detractors / total * 100, 2),
        "total_responses": total,
        "timestamp": datetime.now().isoformat()
    }


async def identify_themes_impl(args: Dict[str, Any]) -> Dict[str, Any]:
    """Identify key themes from feedback"""
    if not HAS_OPENAI:
        return {"error": "OpenAI API not configured"}

    feedbacks = args.get("feedbacks", [])
    max_themes = args.get("max_themes", 5)

    if not feedbacks:
        return {"error": "No feedbacks provided"}

    # Combine feedbacks for theme analysis
    combined = "\n\n".join([f"- {fb}" for fb in feedbacks[:50]])  # Limit to 50 for token limits

    prompt = f"""Analyze these customer feedbacks and identify the top {max_themes} key themes or topics.

Feedbacks:
{combined}

For each theme provide:
1. Theme name
2. Description
3. Number of mentions (estimate)
4. Sentiment associated with this theme
5. Priority level (high/medium/low)

Respond in JSON format with a "themes" array."""

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    analysis = json.loads(response.choices[0].message.content)

    return {
        "themes": analysis.get("themes", []),
        "feedbacks_analyzed": len(feedbacks),
        "timestamp": datetime.now().isoformat()
    }


async def detect_pain_points_impl(args: Dict[str, Any]) -> Dict[str, Any]:
    """Detect customer pain points"""
    if not HAS_OPENAI:
        return {"error": "OpenAI API not configured"}

    feedbacks = args.get("feedbacks", [])
    severity_threshold = args.get("severity_threshold", "medium")

    if not feedbacks:
        return {"error": "No feedbacks provided"}

    combined = "\n\n".join([f"- {fb}" for fb in feedbacks[:50]])

    prompt = f"""Identify customer pain points and issues from these feedbacks.

Feedbacks:
{combined}

For each pain point provide:
1. Issue description
2. Severity level (high/medium/low)
3. Frequency (how many customers mentioned it)
4. Impact on customer experience
5. Suggested action

Only include pain points with severity {severity_threshold} or higher.

Respond in JSON format with a "pain_points" array."""

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    analysis = json.loads(response.choices[0].message.content)

    return {
        "pain_points": analysis.get("pain_points", []),
        "severity_threshold": severity_threshold,
        "feedbacks_analyzed": len(feedbacks),
        "timestamp": datetime.now().isoformat()
    }


async def analyze_csv_file_impl(args: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze feedback CSV file"""
    if not HAS_PANDAS:
        return {"error": "Pandas not available"}

    file_path = args.get("file_path")
    text_column = args.get("text_column", "feedback")
    rating_column = args.get("rating_column")

    try:
        # Read CSV
        df = pd.read_csv(file_path)

        if text_column not in df.columns:
            return {"error": f"Column '{text_column}' not found in CSV"}

        # Basic statistics
        total_rows = len(df)
        non_empty = df[text_column].notna().sum()

        result = {
            "file_path": file_path,
            "total_rows": total_rows,
            "non_empty_feedback": int(non_empty),
            "columns": list(df.columns),
            "sample_feedbacks": df[text_column].dropna().head(5).tolist()
        }

        # Add rating statistics if column exists
        if rating_column and rating_column in df.columns:
            ratings = df[rating_column].dropna()
            result["rating_stats"] = {
                "mean": float(ratings.mean()),
                "median": float(ratings.median()),
                "min": float(ratings.min()),
                "max": float(ratings.max()),
                "count": int(len(ratings))
            }

            # Calculate NPS if ratings are 0-10
            if ratings.min() >= 0 and ratings.max() <= 10:
                nps_result = await calculate_nps_impl({"ratings": ratings.tolist()})
                result["nps"] = nps_result

        result["timestamp"] = datetime.now().isoformat()
        return result

    except Exception as e:
        return {"error": f"Failed to read CSV: {str(e)}"}


async def generate_summary_impl(args: Dict[str, Any]) -> Dict[str, Any]:
    """Generate executive summary"""
    if not HAS_OPENAI:
        return {"error": "OpenAI API not configured"}

    feedbacks = args.get("feedbacks", [])
    format_style = args.get("format", "brief")

    if not feedbacks:
        return {"error": "No feedbacks provided"}

    combined = "\n\n".join([f"- {fb}" for fb in feedbacks[:100]])

    format_instructions = {
        "brief": "Provide a 2-3 sentence summary",
        "detailed": "Provide a detailed 2-paragraph summary with key insights",
        "executive": "Provide an executive summary with key findings, recommendations, and metrics"
    }

    prompt = f"""Generate a {format_style} summary of these customer feedbacks.

Feedbacks:
{combined}

{format_instructions[format_style]}

Include:
- Overall sentiment trend
- Key themes
- Critical issues
- Notable positive feedback
- Actionable recommendations

Respond in JSON format with appropriate fields."""

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    summary = json.loads(response.choices[0].message.content)
    summary["format"] = format_style
    summary["feedbacks_analyzed"] = len(feedbacks)
    summary["timestamp"] = datetime.now().isoformat()

    return summary


async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    print("Starting Feedback Analyzer MCP Server...", file=sys.stderr)
    asyncio.run(main())
