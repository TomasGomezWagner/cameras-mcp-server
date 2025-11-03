#!/usr/bin/env python3
"""
Camera Speeding Ticket MCP Server
Analyzes JSON data from GitHub repository containing camera ticket information
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
from statistics import mean, median
import httpx
from pydantic import BaseModel, Field, field_validator, ConfigDict
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cameras_mcp")

# Initialize MCP server
mcp = FastMCP("cameras_mcp")

# Constants
CHARACTER_LIMIT = 25000
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/TomasGomezWagner/equipos-json/main"
GITHUB_TOKEN = os.environ.get(
    "GITHUB_TOKEN", ""
)  # Optional GitHub token for private repos


# === Enums ===
class ResponseFormat(str, Enum):
    """Output format for tool responses."""

    MARKDOWN = "markdown"
    JSON = "json"


class TimeRange(str, Enum):
    """Time range options for analysis."""

    WEEK = "week"
    MONTH = "month"
    ALL = "all"


# === Helper Functions ===


async def fetch_json_from_github(url: str) -> Optional[Dict[str, Any]]:
    """Fetch JSON data from GitHub URL with error handling."""
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching {url}: {e.response.status_code}")
        if e.response.status_code == 404:
            return None
        raise
    except Exception as e:
        logger.error(f"Error fetching {url}: {str(e)}")
        raise


async def get_available_weeks(month_number: int, month_name: str) -> List[int]:
    """Determine available weeks for a given month."""
    available = []
    for week in range(1, 6):  # Max 5 weeks in a month
        url = f"{GITHUB_RAW_BASE}/status/{month_number:02d}-{month_name}/semana{week}.json"
        data = await fetch_json_from_github(url)
        if data:
            available.append(week)
    return available


async def fetch_week_data(
    month_number: int, month_name: str, week_number: int
) -> Optional[Dict[str, Any]]:
    """Fetch data for a specific week."""
    url = f"{GITHUB_RAW_BASE}/status/{month_number:02d}-{month_name}/semana{week_number}.json"
    return await fetch_json_from_github(url)


def format_camera_data_markdown(
    camera_id: str, camera_data: Dict[str, Any], include_daily: bool = False
) -> str:
    """Format camera data as markdown."""
    lines = [
        f"## Camera {camera_id} - {camera_data['camera']}",
        f"- **Uptime**: {camera_data['uptime'].strip()}",
        f"- **Storage Used**: {camera_data['used_storage']}",
        f"- **Total Infractions**: {camera_data['total']}",
    ]

    if include_daily and "infractions" in camera_data:
        lines.append("\n### Daily Infractions:")
        for date, count in camera_data["infractions"].items():
            lines.append(f"- {date}: {count}")

        lines.append("\n### Daily Frames:")
        for date, count in camera_data["frames"].items():
            lines.append(f"- {date}: {count}")

    return "\n".join(lines)


def calculate_statistics(values: List[float]) -> Dict[str, float]:
    """Calculate basic statistics for a list of values."""
    if not values:
        return {"mean": 0, "median": 0, "min": 0, "max": 0, "total": 0}

    return {
        "mean": round(mean(values), 2),
        "median": round(median(values), 2),
        "min": min(values),
        "max": max(values),
        "total": sum(values),
    }


def truncate_response(response: str) -> str:
    """Truncate response if it exceeds CHARACTER_LIMIT."""
    if len(response) <= CHARACTER_LIMIT:
        return response

    truncated = response[: CHARACTER_LIMIT - 200]
    truncated += (
        "\n\n... [Response truncated due to size. Use filters to narrow results.]"
    )
    return truncated


# === Pydantic Models ===


class ListCamerasInput(BaseModel):
    """Input model for listing cameras."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    month_number: int = Field(..., description="Month number (1-12)", ge=1, le=12)
    month_name: str = Field(
        ..., description="Month name in Spanish (e.g., 'enero', 'febrero')"
    )
    week_number: Optional[int] = Field(
        default=None,
        description="Week number (1-5). If not specified, lists all weeks",
        ge=1,
        le=5,
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class GetCameraStatusInput(BaseModel):
    """Input model for getting camera status."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    month_number: int = Field(..., description="Month number (1-12)", ge=1, le=12)
    month_name: str = Field(
        ..., description="Month name in Spanish (e.g., 'enero', 'febrero')"
    )
    week_number: int = Field(..., description="Week number (1-5)", ge=1, le=5)
    camera_id: str = Field(..., description="Camera ID (e.g., '1', '5')")
    include_daily: bool = Field(
        default=False, description="Include daily breakdown of infractions and frames"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class AnalyzeCameraPerformanceInput(BaseModel):
    """Input model for analyzing camera performance."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    month_number: int = Field(..., description="Month number (1-12)", ge=1, le=12)
    month_name: str = Field(
        ..., description="Month name in Spanish (e.g., 'enero', 'febrero')"
    )
    week_number: Optional[int] = Field(
        default=None,
        description="Specific week (1-5) or None for all weeks",
        ge=1,
        le=5,
    )
    camera_id: Optional[str] = Field(
        default=None, description="Specific camera ID or None for all cameras"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class CompareCamerasInput(BaseModel):
    """Input model for comparing cameras."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    month_number: int = Field(..., description="Month number (1-12)", ge=1, le=12)
    month_name: str = Field(
        ..., description="Month name in Spanish (e.g., 'enero', 'febrero')"
    )
    week_number: int = Field(..., description="Week number (1-5)", ge=1, le=5)
    metric: str = Field(
        ...,
        description="Metric to compare: 'infractions', 'frames', 'efficiency' (infractions/frames ratio)",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )

    @field_validator("metric")
    @classmethod
    def validate_metric(cls, v: str) -> str:
        if v not in ["infractions", "frames", "efficiency"]:
            raise ValueError("Metric must be 'infractions', 'frames', or 'efficiency'")
        return v


class SearchInfractionsInput(BaseModel):
    """Input model for searching infractions."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    month_number: int = Field(..., description="Month number (1-12)", ge=1, le=12)
    month_name: str = Field(
        ..., description="Month name in Spanish (e.g., 'enero', 'febrero')"
    )
    date: Optional[str] = Field(
        default=None, description="Specific date (YYYY-MM-DD) to search"
    )
    min_infractions: Optional[int] = Field(
        default=None, description="Minimum number of infractions", ge=0
    )
    max_infractions: Optional[int] = Field(
        default=None, description="Maximum number of infractions", ge=0
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class GetMonthlyReportInput(BaseModel):
    """Input model for monthly report."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    month_number: int = Field(..., description="Month number (1-12)", ge=1, le=12)
    month_name: str = Field(
        ..., description="Month name in Spanish (e.g., 'enero', 'febrero')"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


# === MCP Tools ===


@mcp.tool(
    name="list_cameras",
    annotations={
        "title": "List Available Cameras",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def list_cameras(params: ListCamerasInput) -> str:
    """List all available cameras with basic information.

    Fetches camera data from the GitHub repository and provides a summary
    of all cameras for the specified time period.

    Returns:
        str: Formatted list of cameras with their status and totals
    """
    try:
        cameras_info = []

        if params.week_number:
            # Specific week requested
            data = await fetch_week_data(
                params.month_number, params.month_name, params.week_number
            )
            if not data:
                return f"❌ No data found for week {params.week_number} of {params.month_name}"

            for camera_id, camera_data in data.items():
                cameras_info.append(
                    {
                        "id": camera_id,
                        "name": camera_data["camera"],
                        "total_infractions": camera_data["total"],
                        "storage_used": camera_data["used_storage"],
                        "week": params.week_number,
                    }
                )
        else:
            # All weeks
            available_weeks = await get_available_weeks(
                params.month_number, params.month_name
            )
            if not available_weeks:
                return f"❌ No data found for {params.month_name}"

            for week in available_weeks:
                data = await fetch_week_data(
                    params.month_number, params.month_name, week
                )
                if data:
                    for camera_id, camera_data in data.items():
                        cameras_info.append(
                            {
                                "id": camera_id,
                                "name": camera_data["camera"],
                                "total_infractions": camera_data["total"],
                                "storage_used": camera_data["used_storage"],
                                "week": week,
                            }
                        )

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(
                {"cameras": cameras_info, "count": len(cameras_info)}, indent=2
            )

        # Markdown format
        lines = [f"# Cameras for {params.month_name.capitalize()}"]
        if params.week_number:
            lines.append(f"## Week {params.week_number}")
        else:
            lines.append(f"## Available Weeks: {', '.join(map(str, available_weeks))}")

        lines.append(
            f"\nTotal cameras found: {len(set(c['id'] for c in cameras_info))}\n"
        )

        # Group by camera ID
        by_camera = {}
        for info in cameras_info:
            if info["id"] not in by_camera:
                by_camera[info["id"]] = []
            by_camera[info["id"]].append(info)

        for camera_id in sorted(by_camera.keys()):
            camera_infos = by_camera[camera_id]
            lines.append(f"### Camera {camera_id} - {camera_infos[0]['name']}")
            for info in camera_infos:
                lines.append(
                    f"- Week {info['week']}: {info['total_infractions']} infractions, Storage: {info['storage_used']}"
                )

        return truncate_response("\n".join(lines))

    except Exception as e:
        logger.error(f"Error listing cameras: {str(e)}")
        return f"❌ Error: {str(e)}"


@mcp.tool(
    name="get_camera_status",
    annotations={
        "title": "Get Camera Status",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def get_camera_status(params: GetCameraStatusInput) -> str:
    """Get detailed status for a specific camera.

    Retrieves comprehensive information about a camera including uptime,
    storage usage, and infraction statistics.

    Returns:
        str: Detailed camera status information
    """
    try:
        data = await fetch_week_data(
            params.month_number, params.month_name, params.week_number
        )
        if not data:
            return (
                f"❌ No data found for week {params.week_number} of {params.month_name}"
            )

        if params.camera_id not in data:
            return (
                f"❌ Camera {params.camera_id} not found in week {params.week_number}"
            )

        camera_data = data[params.camera_id]

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(camera_data, indent=2)

        # Markdown format
        return format_camera_data_markdown(
            params.camera_id, camera_data, params.include_daily
        )

    except Exception as e:
        logger.error(f"Error getting camera status: {str(e)}")
        return f"❌ Error: {str(e)}"


@mcp.tool(
    name="analyze_camera_performance",
    annotations={
        "title": "Analyze Camera Performance",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def analyze_camera_performance(params: AnalyzeCameraPerformanceInput) -> str:
    """Analyze performance metrics for cameras.

    Provides statistical analysis including averages, totals, and trends
    for camera infractions and frame captures.

    Returns:
        str: Performance analysis with statistics
    """
    try:
        weeks_to_analyze = []

        if params.week_number:
            weeks_to_analyze = [params.week_number]
        else:
            weeks_to_analyze = await get_available_weeks(
                params.month_number, params.month_name
            )

        if not weeks_to_analyze:
            return f"❌ No data found for {params.month_name}"

        # Collect all data
        all_data = {}
        for week in weeks_to_analyze:
            data = await fetch_week_data(params.month_number, params.month_name, week)
            if data:
                for camera_id, camera_data in data.items():
                    if params.camera_id and camera_id != params.camera_id:
                        continue

                    if camera_id not in all_data:
                        all_data[camera_id] = {
                            "name": camera_data["camera"],
                            "weeks": [],
                            "infractions": [],
                            "frames": [],
                            "daily_infractions": {},
                            "daily_frames": {},
                        }

                    all_data[camera_id]["weeks"].append(week)
                    all_data[camera_id]["infractions"].append(camera_data["total"])

                    # Aggregate daily data
                    for date, count in camera_data.get("infractions", {}).items():
                        if date not in all_data[camera_id]["daily_infractions"]:
                            all_data[camera_id]["daily_infractions"][date] = 0
                        all_data[camera_id]["daily_infractions"][date] += count

                    for date, count in camera_data.get("frames", {}).items():
                        if date not in all_data[camera_id]["daily_frames"]:
                            all_data[camera_id]["daily_frames"][date] = 0
                        all_data[camera_id]["daily_frames"][date] += count

        if not all_data:
            return f"❌ No data found for the specified criteria"

        # Calculate statistics
        analysis = {}
        for camera_id, data in all_data.items():
            infraction_stats = calculate_statistics(data["infractions"])

            # Calculate daily averages
            daily_infraction_values = list(data["daily_infractions"].values())
            daily_frame_values = list(data["daily_frames"].values())

            analysis[camera_id] = {
                "name": data["name"],
                "weeks_analyzed": len(data["weeks"]),
                "infraction_stats": infraction_stats,
                "daily_infraction_avg": (
                    round(mean(daily_infraction_values), 2)
                    if daily_infraction_values
                    else 0
                ),
                "daily_frame_avg": (
                    round(mean(daily_frame_values), 2) if daily_frame_values else 0
                ),
                "efficiency": (
                    round(
                        sum(daily_infraction_values) / sum(daily_frame_values) * 100, 2
                    )
                    if sum(daily_frame_values) > 0
                    else 0
                ),
            }

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(analysis, indent=2)

        # Markdown format
        lines = [f"# Performance Analysis - {params.month_name.capitalize()}"]

        if params.week_number:
            lines.append(f"## Week {params.week_number}")
        else:
            lines.append(f"## Weeks Analyzed: {', '.join(map(str, weeks_to_analyze))}")

        for camera_id, stats in analysis.items():
            lines.extend(
                [
                    f"\n### Camera {camera_id} - {stats['name']}",
                    f"- **Weeks Analyzed**: {stats['weeks_analyzed']}",
                    f"- **Infraction Statistics**:",
                    f"  - Mean: {stats['infraction_stats']['mean']}",
                    f"  - Median: {stats['infraction_stats']['median']}",
                    f"  - Min: {stats['infraction_stats']['min']}",
                    f"  - Max: {stats['infraction_stats']['max']}",
                    f"  - Total: {stats['infraction_stats']['total']}",
                    f"- **Daily Averages**:",
                    f"  - Infractions: {stats['daily_infraction_avg']}",
                    f"  - Frames: {stats['daily_frame_avg']}",
                    f"- **Efficiency Rate**: {stats['efficiency']}%",
                ]
            )

        return truncate_response("\n".join(lines))

    except Exception as e:
        logger.error(f"Error analyzing performance: {str(e)}")
        return f"❌ Error: {str(e)}"


@mcp.tool(
    name="compare_cameras",
    annotations={
        "title": "Compare Cameras",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def compare_cameras(params: CompareCamerasInput) -> str:
    """Compare cameras based on specific metrics.

    Provides side-by-side comparison of cameras for infractions, frames,
    or efficiency metrics.

    Returns:
        str: Comparison results sorted by the specified metric
    """
    try:
        data = await fetch_week_data(
            params.month_number, params.month_name, params.week_number
        )
        if not data:
            return (
                f"❌ No data found for week {params.week_number} of {params.month_name}"
            )

        # Calculate metrics for each camera
        comparisons = []
        for camera_id, camera_data in data.items():
            total_infractions = camera_data["total"]
            total_frames = sum(camera_data.get("frames", {}).values())

            metric_value = 0
            if params.metric == "infractions":
                metric_value = total_infractions
            elif params.metric == "frames":
                metric_value = total_frames
            elif params.metric == "efficiency":
                metric_value = (
                    (total_infractions / total_frames * 100) if total_frames > 0 else 0
                )

            comparisons.append(
                {
                    "id": camera_id,
                    "name": camera_data["camera"],
                    "infractions": total_infractions,
                    "frames": total_frames,
                    "efficiency": (
                        (total_infractions / total_frames * 100)
                        if total_frames > 0
                        else 0
                    ),
                    "metric_value": metric_value,
                    "storage": camera_data["used_storage"],
                }
            )

        # Sort by metric value
        comparisons.sort(key=lambda x: x["metric_value"], reverse=True)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(
                {
                    "metric": params.metric,
                    "week": params.week_number,
                    "cameras": comparisons,
                },
                indent=2,
            )

        # Markdown format
        lines = [
            f"# Camera Comparison - {params.month_name.capitalize()} Week {params.week_number}",
            f"## Metric: {params.metric.capitalize()}",
            f"\n| Rank | Camera | {params.metric.capitalize()} | Infractions | Frames | Efficiency | Storage |",
            "|------|--------|"
            + "-" * len(params.metric)
            + "|-------------|--------|------------|---------|",
        ]

        for i, comp in enumerate(comparisons, 1):
            metric_display = (
                f"{comp['metric_value']:.2f}"
                if params.metric == "efficiency"
                else str(int(comp["metric_value"]))
            )
            lines.append(
                f"| {i} | {comp['name']} (ID: {comp['id']}) | {metric_display} | "
                f"{comp['infractions']} | {comp['frames']} | {comp['efficiency']:.2f}% | {comp['storage']} |"
            )

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Error comparing cameras: {str(e)}")
        return f"❌ Error: {str(e)}"


@mcp.tool(
    name="search_infractions",
    annotations={
        "title": "Search Infractions",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def search_infractions(params: SearchInfractionsInput) -> str:
    """Search for infractions based on criteria.

    Finds cameras and dates matching specific infraction criteria such as
    date ranges or infraction count thresholds.

    Returns:
        str: Matching infractions with camera and date information
    """
    try:
        available_weeks = await get_available_weeks(
            params.month_number, params.month_name
        )
        if not available_weeks:
            return f"❌ No data found for {params.month_name}"

        matches = []

        for week in available_weeks:
            data = await fetch_week_data(params.month_number, params.month_name, week)
            if not data:
                continue

            for camera_id, camera_data in data.items():
                infractions = camera_data.get("infractions", {})

                for date, count in infractions.items():
                    # Check date filter
                    if params.date and date != params.date:
                        continue

                    # Check min/max filters
                    if (
                        params.min_infractions is not None
                        and count < params.min_infractions
                    ):
                        continue
                    if (
                        params.max_infractions is not None
                        and count > params.max_infractions
                    ):
                        continue

                    matches.append(
                        {
                            "week": week,
                            "camera_id": camera_id,
                            "camera_name": camera_data["camera"],
                            "date": date,
                            "infractions": count,
                            "frames": camera_data.get("frames", {}).get(date, 0),
                        }
                    )

        # Sort by date and infractions
        matches.sort(key=lambda x: (x["date"], -x["infractions"]))

        if params.response_format == ResponseFormat.JSON:
            return json.dumps({"matches": matches, "count": len(matches)}, indent=2)

        # Markdown format
        lines = [f"# Infraction Search Results - {params.month_name.capitalize()}"]

        filters = []
        if params.date:
            filters.append(f"Date: {params.date}")
        if params.min_infractions is not None:
            filters.append(f"Min: {params.min_infractions}")
        if params.max_infractions is not None:
            filters.append(f"Max: {params.max_infractions}")

        if filters:
            lines.append(f"## Filters: {', '.join(filters)}")

        lines.append(f"\nFound {len(matches)} matching records\n")

        if matches:
            # Group by date
            by_date = {}
            for match in matches:
                if match["date"] not in by_date:
                    by_date[match["date"]] = []
                by_date[match["date"]].append(match)

            for date in sorted(by_date.keys()):
                lines.append(f"\n### {date}")
                for match in by_date[date]:
                    lines.append(
                        f"- **{match['camera_name']}** (ID: {match['camera_id']}, Week {match['week']}): "
                        f"{match['infractions']} infractions, {match['frames']} frames"
                    )
        else:
            lines.append("No matches found")

        return truncate_response("\n".join(lines))

    except Exception as e:
        logger.error(f"Error searching infractions: {str(e)}")
        return f"❌ Error: {str(e)}"


@mcp.tool(
    name="get_monthly_report",
    annotations={
        "title": "Get Monthly Report",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def get_monthly_report(params: GetMonthlyReportInput) -> str:
    """Generate a comprehensive monthly report.

    Creates a complete analysis of all cameras for the entire month including
    totals, averages, trends, and top performers.

    Returns:
        str: Comprehensive monthly report with all statistics
    """
    try:
        available_weeks = await get_available_weeks(
            params.month_number, params.month_name
        )
        if not available_weeks:
            return f"❌ No data found for {params.month_name}"

        # Aggregate all month data
        month_data = {
            "total_infractions": 0,
            "total_frames": 0,
            "cameras": {},
            "daily_totals": {},
            "week_summaries": [],
        }

        for week in available_weeks:
            data = await fetch_week_data(params.month_number, params.month_name, week)
            if not data:
                continue

            week_infractions = 0
            week_frames = 0

            for camera_id, camera_data in data.items():
                # Initialize camera if first time seeing it
                if camera_id not in month_data["cameras"]:
                    month_data["cameras"][camera_id] = {
                        "name": camera_data["camera"],
                        "total_infractions": 0,
                        "total_frames": 0,
                        "weeks_active": 0,
                    }

                # Update camera totals
                month_data["cameras"][camera_id]["total_infractions"] += camera_data[
                    "total"
                ]
                month_data["cameras"][camera_id]["weeks_active"] += 1

                # Update daily totals
                for date, count in camera_data.get("infractions", {}).items():
                    if date not in month_data["daily_totals"]:
                        month_data["daily_totals"][date] = {
                            "infractions": 0,
                            "frames": 0,
                        }
                    month_data["daily_totals"][date]["infractions"] += count
                    week_infractions += count

                for date, count in camera_data.get("frames", {}).items():
                    if date not in month_data["daily_totals"]:
                        month_data["daily_totals"][date] = {
                            "infractions": 0,
                            "frames": 0,
                        }
                    month_data["daily_totals"][date]["frames"] += count
                    week_frames += count
                    month_data["cameras"][camera_id]["total_frames"] += count

            month_data["week_summaries"].append(
                {"week": week, "infractions": week_infractions, "frames": week_frames}
            )

            month_data["total_infractions"] += week_infractions
            month_data["total_frames"] += week_frames

        # Calculate top performers
        camera_rankings = sorted(
            month_data["cameras"].items(),
            key=lambda x: x[1]["total_infractions"],
            reverse=True,
        )

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(
                {
                    "month": params.month_name,
                    "summary": {
                        "total_infractions": month_data["total_infractions"],
                        "total_frames": month_data["total_frames"],
                        "efficiency": (
                            round(
                                month_data["total_infractions"]
                                / month_data["total_frames"]
                                * 100,
                                2,
                            )
                            if month_data["total_frames"] > 0
                            else 0
                        ),
                        "weeks_available": len(available_weeks),
                        "cameras_active": len(month_data["cameras"]),
                    },
                    "cameras": month_data["cameras"],
                    "week_summaries": month_data["week_summaries"],
                },
                indent=2,
            )

        # Markdown format
        lines = [
            f"# Monthly Report - {params.month_name.capitalize()} {datetime.now().year}",
            f"\n## Executive Summary",
            f"- **Total Infractions**: {month_data['total_infractions']:,}",
            f"- **Total Frames**: {month_data['total_frames']:,}",
            f"- **Overall Efficiency**: {round(month_data['total_infractions'] / month_data['total_frames'] * 100, 2) if month_data['total_frames'] > 0 else 0}%",
            f"- **Weeks Analyzed**: {len(available_weeks)} ({', '.join(map(str, available_weeks))})",
            f"- **Active Cameras**: {len(month_data['cameras'])}",
            f"\n## Weekly Breakdown",
        ]

        for summary in month_data["week_summaries"]:
            efficiency = (
                round(summary["infractions"] / summary["frames"] * 100, 2)
                if summary["frames"] > 0
                else 0
            )
            lines.append(
                f"- **Week {summary['week']}**: {summary['infractions']} infractions, "
                f"{summary['frames']} frames (Efficiency: {efficiency}%)"
            )

        lines.append("\n## Top Performing Cameras")
        for i, (camera_id, camera_stats) in enumerate(camera_rankings[:5], 1):
            efficiency = (
                round(
                    camera_stats["total_infractions"]
                    / camera_stats["total_frames"]
                    * 100,
                    2,
                )
                if camera_stats["total_frames"] > 0
                else 0
            )
            lines.append(
                f"{i}. **{camera_stats['name']}** (ID: {camera_id}): "
                f"{camera_stats['total_infractions']} infractions, "
                f"{camera_stats['total_frames']} frames, "
                f"Efficiency: {efficiency}%"
            )

        # Daily trend (last 7 days with data)
        sorted_dates = sorted(month_data["daily_totals"].keys())[-7:]
        if sorted_dates:
            lines.append("\n## Recent Daily Trends (Last 7 Days with Data)")
            for date in sorted_dates:
                daily = month_data["daily_totals"][date]
                lines.append(
                    f"- **{date}**: {daily['infractions']} infractions, {daily['frames']} frames"
                )

        return truncate_response("\n".join(lines))

    except Exception as e:
        logger.error(f"Error generating monthly report: {str(e)}")
        return f"❌ Error: {str(e)}"


@mcp.tool(
    name="fetch_raw_url",
    annotations={
        "title": "Fetch Raw URL",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def fetch_raw_url(url: str) -> str:
    """Fetch raw content from a URL and return it as-is.

    Makes a simple HTTP GET request to the specified URL and returns
    the raw response body without any processing.

    Args:
        url: The URL to fetch (e.g., https://raw.githubusercontent.com/...)

    Returns:
        str: Raw response content from the URL
    """
    try:
        headers = {}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=60.0)
            response.raise_for_status()
            return response.text

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching {url}: {e.response.status_code}")
        return f"❌ HTTP Error {e.response.status_code}: {e.response.text[:200]}"
    except httpx.TimeoutException:
        logger.error(f"Timeout fetching {url}")
        return f"❌ Timeout Error: Request took longer than 10 seconds"
    except Exception as e:
        logger.error(f"Error fetching {url}: {str(e)}")
        return f"❌ Error: {str(e)}"


# === Health Check Tool (for monitoring) ===


@mcp.tool(
    name="health_check",
    annotations={
        "title": "Health Check",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def health_check() -> str:
    """Health check endpoint for monitoring.

    Returns:
        str: Server status information
    """
    return json.dumps(
        {
            "status": "healthy",
            "service": "cameras_mcp",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "github_token": "configured" if GITHUB_TOKEN else "not configured",
        },
        indent=2,
    )


# === Server Startup ===
if __name__ == "__main__":
    logger.info("Starting Camera Speeding Ticket MCP Server...")

    # Get port from environment variable (Render sets this)
    port = int(os.environ.get("PORT", 8000))

    if GITHUB_TOKEN:
        logger.info("GitHub token detected - private repository access enabled")
    else:
        logger.info("No GitHub token found - only public repository access available")

    logger.info(f"Server will start on port {port}")

    try:
        # Use HTTP transport for web deployment
        mcp.run(transport="sse")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        import sys

        sys.exit(1)
