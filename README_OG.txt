# Camera Speeding Ticket MCP Server

A Model Context Protocol (MCP) server that analyzes JSON data from a GitHub repository containing camera speeding ticket information. It provides comprehensive tools for querying camera status, analyzing performance metrics, and generating reports.

## Purpose

This MCP server provides a secure interface for AI assistants to analyze camera speeding ticket data stored in JSON files on GitHub. It enables complex queries about camera performance, infractions, efficiency rates, and trends over time.

## Features

### Current Implementation

- **`list_cameras`** - Lists all available cameras with basic information for a specific month/week
- **`get_camera_status`** - Retrieves detailed status for a specific camera including uptime and storage
- **`analyze_camera_performance`** - Analyzes performance metrics with statistical calculations
- **`compare_cameras`** - Compares cameras based on infractions, frames, or efficiency metrics
- **`search_infractions`** - Searches for infractions based on date, count thresholds, or other criteria
- **`get_monthly_report`** - Generates comprehensive monthly reports with trends and top performers

## Data Structure

The server reads JSON files from the GitHub repository with this structure:
- URL Pattern: `https://raw.githubusercontent.com/TomasGomezWagner/equipos-json/refs/heads/main/status/<month_number>-<month_name>/semana<week_number>.json`
- Each file contains camera data with infractions, frames, uptime, and storage information
- Supports both public and private repository access (with GitHub token)

## Prerequisites

- Docker Desktop with MCP Toolkit enabled
- Docker MCP CLI plugin (`docker mcp` command)
- GitHub personal access token (optional, for private repository access)

## Installation

See the step-by-step instructions provided with the files.

## Usage Examples

In Claude Desktop, you can ask:

### Basic Queries
- "List all cameras for octubre week 1"
- "What's the status of camera 5 in september week 3?"
- "Show me cameras with more than 50 infractions in a single day"

### Analysis Queries
- "Analyze the performance of all cameras for the entire month of octubre"
- "Compare all cameras in week 2 based on efficiency"
- "What's the average number of daily infractions for camera 1?"

### Reporting Queries
- "Generate a monthly report for septiembre"
- "Show me the top performing cameras last month"
- "Find all dates where camera 3 had zero infractions"

### Advanced Queries
- "Which camera has the highest efficiency rate (infractions per frame)?"
- "Show me the trend of infractions over the last 4 weeks"
- "Find cameras that had more than 100 infractions in week 1"

## Architecture

```
Claude Desktop → MCP Gateway → Cameras MCP Server → GitHub Repository
                      ↓
              Docker Desktop Secrets
               (GITHUB_TOKEN)
```

## Development

### Local Testing

```bash
# Set environment variables for testing (optional)
export GITHUB_TOKEN="your-github-token"

# Run directly
python cameras_mcp.py

# Test MCP protocol
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python cameras_mcp.py
```

### Adding New Tools

1. Add the function to cameras_mcp.py
2. Create a Pydantic model for input validation
3. Decorate with @mcp.tool() and proper annotations
4. Update the catalog entry with the new tool name
5. Rebuild the Docker image

### Data Format

The server expects JSON files with this structure:
```json
{
    "1": {
        "camera": "uno",
        "uptime": "05:52:18 up 2 days...",
        "used_storage": "49%",
        "total": 98,
        "infractions": {
            "2025-09-29": 32,
            "2025-09-30": 18
        },
        "frames": {
            "2025-09-29": 178,
            "2025-09-30": 128
        }
    }
}
```

## Troubleshooting

### Tools Not Appearing
- Verify Docker image built successfully
- Check catalog and registry files
- Ensure Claude Desktop config includes custom catalog
- Restart Claude Desktop

### Authentication Errors
- Verify GitHub token with `docker mcp secret list`
- Ensure token has repo read permissions
- Check if repository is public or private

### No Data Found
- Verify the repository URL is correct
- Check that JSON files exist in expected paths
- Ensure month names are in Spanish (enero, febrero, etc.)
- Confirm week numbers are within valid range (1-5)

### Performance Issues
- Large datasets are automatically truncated at 25,000 characters
- Use specific week/camera filters to reduce data
- Consider implementing pagination for large results

## Security Considerations

- GitHub token stored securely in Docker Desktop secrets
- Never hardcode credentials
- Running as non-root user in container
- Sensitive data never logged
- Read-only operations only

## Response Formats

The server supports two output formats:

### Markdown Format (default)
- Human-readable with headers, lists, and tables
- Ideal for direct consumption by users
- Includes formatting for better readability

### JSON Format
- Machine-readable structured data
- Complete data suitable for programmatic processing
- Includes all available fields and metadata

## Tool Annotations

All tools are configured with appropriate MCP annotations:
- `readOnlyHint: true` - All operations are read-only
- `destructiveHint: false` - No destructive operations
- `idempotentHint: true` - Repeated calls have same effect
- `openWorldHint: true` - Interacts with external GitHub repository

## License

MIT License

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify GitHub repository accessibility
3. Ensure JSON files follow expected format
4. Review Docker logs for detailed error messages
