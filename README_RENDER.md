# Camera Speeding Ticket MCP Server - Web Deployment

A public MCP server that analyzes camera speeding ticket data, deployable on Render or any web hosting platform.

## 🚀 Quick Deploy to Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

## 📦 What This Server Does

This MCP server provides tools to analyze camera speeding ticket data from a GitHub repository:

- **List cameras** - View all available cameras with their statistics
- **Get camera status** - Detailed information about specific cameras
- **Analyze performance** - Statistical analysis with averages and trends
- **Compare cameras** - Side-by-side comparison by various metrics
- **Search infractions** - Find patterns and anomalies
- **Generate reports** - Comprehensive monthly summaries

## 🔧 Manual Deployment on Render

### Step 1: Fork or Clone This Repository

Create your own copy of this repository on GitHub.

### Step 2: Create Render Account

Sign up at [render.com](https://render.com) if you don't have an account.

### Step 3: Create New Web Service

1. Go to your Render Dashboard
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `cameras-mcp-server`
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements_web.txt`
   - **Start Command**: `python cameras_mcp_web.py`

### Step 4: Set Environment Variables (Optional)

If the GitHub repository becomes private, add:
- **Key**: `GITHUB_TOKEN`
- **Value**: Your GitHub personal access token

### Step 5: Deploy

Click "Create Web Service" and wait for deployment.

## 🌐 Using the Deployed Server

### With Claude Desktop

Once deployed, add this to your Claude Desktop config:

```json
{
  "mcpServers": {
    "cameras-remote": {
      "url": "https://your-service-name.onrender.com",
      "transport": "sse"
    }
  }
}
```

### API Endpoints

The server exposes MCP tools via Server-Sent Events (SSE):

- **Base URL**: `https://your-service-name.onrender.com`
- **Protocol**: MCP over SSE
- **Tools Available**:
  - `list_cameras`
  - `get_camera_status`
  - `analyze_camera_performance`
  - `compare_cameras`
  - `search_infractions`
  - `get_monthly_report`

### Example Tool Calls

```javascript
// Example: List cameras for October
{
  "tool": "list_cameras",
  "arguments": {
    "month_number": 10,
    "month_name": "octubre",
    "response_format": "json"
  }
}

// Example: Get monthly report
{
  "tool": "get_monthly_report",
  "arguments": {
    "month_number": 9,
    "month_name": "septiembre",
    "response_format": "markdown"
  }
}
```

## 📊 Data Source

The server reads data from:
- **Repository**: https://github.com/TomasGomezWagner/equipos-json
- **Structure**: `/status/{month_number}-{month_name}/semana{week_number}.json`
- **Format**: JSON files with camera infractions and frame data

### Data Format Example

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

## 🔒 Security

- Read-only operations only
- Optional GitHub token for private repos
- No data storage or modification
- Rate limiting built-in

## 🛠️ Local Development

### Prerequisites
- Python 3.11+
- pip

### Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd cameras-mcp-server

# Install dependencies
pip install -r requirements_web.txt

# Run locally
python cameras_mcp_web.py
```

The server will start on `http://localhost:8000`

### Testing

```bash
# Test the server
curl http://localhost:8000/health

# Test MCP protocol
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | \
  curl -X POST http://localhost:8000 -H "Content-Type: application/json" -d @-
```

## 📝 Environment Variables

- `PORT` - Port to run the server (default: 8000, auto-set by Render)
- `GITHUB_TOKEN` - Optional GitHub token for private repository access

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🆘 Troubleshooting

### Server Not Starting
- Check logs in Render dashboard
- Verify Python version is 3.11+
- Ensure all dependencies are installed

### No Data Found
- Verify GitHub repository is accessible
- Check month names are in Spanish
- Confirm week numbers exist (1-5)

### Authentication Issues
- If repo is private, add GITHUB_TOKEN
- Verify token has repository read permissions

## 📞 Support

For issues or questions:
- Open an issue on GitHub
- Check Render logs for error details
- Verify data source repository is accessible

## 🎯 Use Cases

Perfect for:
- Traffic analysis dashboards
- Performance monitoring
- Infraction trend analysis
- Camera efficiency reports
- Public safety analytics

## 🔗 Links

- [MCP Protocol Documentation](https://modelcontextprotocol.io)
- [Render Documentation](https://render.com/docs)
- [Data Source Repository](https://github.com/TomasGomezWagner/equipos-json)

---

**Note**: This is a read-only service that analyzes publicly available data. No camera control or modification capabilities are included.
