# Camera Speeding Ticket MCP Server - Implementation Guide

## Overview

This MCP server analyzes camera speeding ticket data from a GitHub repository containing JSON files with daily infraction and frame capture statistics.

## Architecture Decisions

### Design Philosophy
- **Workflow-Oriented Tools**: Tools focus on complete analytical workflows rather than just data fetching
- **Statistical Analysis**: Built-in calculations for mean, median, efficiency rates
- **Flexible Querying**: Support for various time ranges and filtering options
- **Performance Optimization**: Character limits and truncation for large datasets

### Data Access Pattern
- Fetches data directly from GitHub raw content URLs
- Supports both public and private repositories (with token)
- Caches nothing - always fetches fresh data
- Handles missing data gracefully

## Tool Design Rationale

### list_cameras
- Provides overview of all cameras
- Supports both single week and full month queries
- Groups results by camera for clarity

### get_camera_status
- Detailed view of single camera
- Optional daily breakdown for granular analysis
- Shows uptime and storage metrics

### analyze_camera_performance
- Statistical analysis with mean, median, min, max
- Calculates efficiency rates (infractions/frames)
- Supports single camera or comparative analysis

### compare_cameras
- Side-by-side comparison with ranking
- Multiple metrics: infractions, frames, efficiency
- Markdown table format for easy reading

### search_infractions
- Flexible searching with multiple criteria
- Date-based and threshold-based filtering
- Groups results by date for temporal analysis

### get_monthly_report
- Executive summary with key metrics
- Weekly breakdowns and trends
- Top performer identification

## Input Validation Strategy

All inputs use Pydantic models with:
- Strict validation for month numbers (1-12)
- Week number constraints (1-5)
- Spanish month names (as per repository structure)
- Optional parameters with sensible defaults
- Response format selection (Markdown/JSON)

## Error Handling Approach

### Network Errors
- Specific handling for 404 (data not found)
- Timeout protection (10 seconds)
- Clear error messages indicating which data is missing

### Data Validation
- Graceful handling of missing fields
- Zero-division protection in efficiency calculations
- Safe aggregation of partial data

## Response Formatting

### Markdown Format
- Headers for organization
- Tables for comparisons
- Lists for enumerations
- Bold text for emphasis
- Truncation message when exceeding limits

### JSON Format
- Complete structured data
- Consistent field naming
- Nested objects for relationships
- Arrays for collections

## Performance Considerations

### Character Limits
- 25,000 character limit per response
- Automatic truncation with notification
- Suggestion to use filters for large datasets

### Efficiency Optimizations
- Parallel fetching where possible
- Early termination on errors
- Minimal data transformation

## Testing Strategies

### Unit Testing
```python
# Test data fetching
assert await fetch_json_from_github(valid_url) is not None
assert await fetch_json_from_github(invalid_url) is None

# Test statistics
assert calculate_statistics([1,2,3])["mean"] == 2.0
assert calculate_statistics([])["mean"] == 0
```

### Integration Testing
```bash
# Test each tool
echo '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"list_cameras","arguments":{"month_number":10,"month_name":"octubre"}},"id":1}' | python cameras_mcp.py
```

## Common Usage Patterns

### Monthly Analysis Workflow
1. List cameras for the month
2. Analyze performance for interesting cameras
3. Compare top performers
4. Generate monthly report

### Problem Investigation Workflow
1. Search for anomalies (zero infractions, high counts)
2. Get detailed status for problematic cameras
3. Compare with other cameras
4. Analyze trends over time

## Extension Points

### Adding New Metrics
- Extend analysis tools with new calculations
- Add new comparison metrics
- Include additional statistics

### Supporting New Data Sources
- Modify fetch functions for different URLs
- Support multiple repository formats
- Add local file support option

### Enhanced Filtering
- Date range queries (not just single dates)
- Camera group filtering
- Percentile-based thresholds

## Implementation Best Practices

### Code Organization
- Helper functions separated from tools
- Clear separation of concerns
- Reusable formatting functions
- Consistent error handling patterns

### Documentation
- Comprehensive docstrings for all tools
- Clear parameter descriptions with examples
- Return type specifications
- Usage scenarios included

### Type Safety
- Full Pydantic validation
- Type hints throughout
- Enum for constrained choices
- No manual string validation

## Troubleshooting Guide

### Common Issues

1. **No data found**
   - Check month name spelling (Spanish)
   - Verify week number exists
   - Confirm repository structure

2. **Authentication failures**
   - Verify GitHub token is set
   - Check token permissions
   - Test with public repository first

3. **Performance problems**
   - Use specific filters
   - Request single weeks instead of months
   - Enable JSON format for large datasets

## Future Enhancements

### Planned Features
- Caching for frequently accessed data
- Trend analysis across months
- Predictive analytics
- Alert generation for anomalies

### Potential Optimizations
- Batch fetching for multiple weeks
- Response streaming for large datasets
- Background data refresh
- Connection pooling for requests

## Security Considerations

### Token Management
- Environment variable for GitHub token
- Never log sensitive information
- Token validation on startup

### Data Protection
- Read-only operations only
- No data modification capabilities
- No local data storage

## Maintenance Notes

### Repository Structure Changes
If the GitHub repository structure changes:
1. Update URL patterns in constants
2. Modify fetch functions
3. Adjust data parsing logic
4. Update documentation

### Adding Authentication Methods
To support different auth methods:
1. Add configuration options
2. Implement auth headers
3. Handle auth errors
4. Update security documentation

## Evaluation Criteria

The server is designed to excel at:
1. Complex multi-step queries
2. Statistical analysis
3. Trend identification
4. Comparative analysis
5. Report generation

## Model Interaction Guidelines

When used by AI models, the server expects:
- Clear specification of time periods
- Spanish month names
- Specific camera IDs when known
- Metric selection for comparisons
- Format preference indication
