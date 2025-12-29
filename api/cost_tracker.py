"""
Hopwise Cost Tracker Service
=============================
Tracks all API calls, calculates costs based on Google's pricing tiers,
and provides endpoints for the dashboard.

Usage:
    1. Import and initialize: tracker = CostTracker()
    2. Log each API call: tracker.log_api_call("places_text_search", details={...})
    3. Get daily/monthly reports via endpoints

Google Places API Pricing (as of Dec 2024):
- Prices are per 1,000 requests AFTER free tier exhausted
- $200/month credit applies to costs after free caps
- Free caps reset on 1st of each month (midnight Pacific)
"""

import json
import os
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
from collections import defaultdict
import threading

# ============================================
# PRICING CONFIGURATION - Update if Google changes pricing
# ============================================

GOOGLE_PLACES_PRICING = {
    # SKU: (free_cap_per_month, cost_per_1000_after_free)
    # Essentials Tier
    "autocomplete": {"free_cap": 10000, "cost_per_1000": 2.83, "tier": "essentials"},
    "geocoding": {"free_cap": 10000, "cost_per_1000": 5.00, "tier": "essentials"},
    "geolocation": {"free_cap": 10000, "cost_per_1000": 5.00, "tier": "essentials"},
    "place_details_essentials": {"free_cap": 10000, "cost_per_1000": 5.00, "tier": "essentials"},
    "text_search_ids_only": {"free_cap": float('inf'), "cost_per_1000": 0.00, "tier": "essentials"},  # Unlimited free
    "time_zone": {"free_cap": 10000, "cost_per_1000": 5.00, "tier": "essentials"},
    
    # Pro Tier
    "nearby_search_pro": {"free_cap": 5000, "cost_per_1000": 32.00, "tier": "pro"},
    "text_search_pro": {"free_cap": 5000, "cost_per_1000": 32.00, "tier": "pro"},
    "place_details_pro": {"free_cap": 5000, "cost_per_1000": 17.00, "tier": "pro"},
    
    # Enterprise Tier
    "nearby_search_enterprise": {"free_cap": 1000, "cost_per_1000": 35.00, "tier": "enterprise"},
    "text_search_enterprise": {"free_cap": 1000, "cost_per_1000": 35.00, "tier": "enterprise"},
    "place_details_enterprise": {"free_cap": 1000, "cost_per_1000": 20.00, "tier": "enterprise"},
    "place_photos": {"free_cap": 1000, "cost_per_1000": 7.00, "tier": "enterprise"},
}

# Static costs (annual)
STATIC_COSTS = {
    "domain": {"cost": 15.99, "frequency": "annual", "provider": "Hostinger", "description": "hopwise.app"},
    "email": {"cost": 4.20, "frequency": "annual", "provider": "Hostinger", "description": "hello@hopwise.app"},
    "hosting_vercel": {"cost": 0.00, "frequency": "monthly", "provider": "Vercel", "description": "Free tier (frontend)"},
    "hosting_railway": {"cost": 0.00, "frequency": "monthly", "provider": "Railway", "description": "Free tier (backend)"},
    "hosting_netlify": {"cost": 0.00, "frequency": "monthly", "provider": "Netlify", "description": "Suspended (marketing page)"},
}

# Monthly credit from Google
GOOGLE_MONTHLY_CREDIT = 200.00

# Budget thresholds for alerts
ALERT_THRESHOLDS = {
    "warning": 0.70,  # 70% of budget
    "critical": 0.90,  # 90% of budget
}


@dataclass
class APICallLog:
    """Single API call record"""
    timestamp: str
    api_type: str
    endpoint: str
    request_count: int
    estimated_cost: float
    details: Optional[Dict] = None
    
    def to_dict(self):
        return asdict(self)


class CostTracker:
    """
    Main cost tracking service for Hopwise.
    Thread-safe logging and cost calculation.
    """
    
    def __init__(self, data_dir: str = "./cost_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        
        # In-memory cache for current month's data
        self._monthly_cache: Dict[str, int] = defaultdict(int)
        self._load_current_month_cache()
    
    def _get_month_key(self, dt: Optional[datetime] = None) -> str:
        """Get YYYY-MM key for a datetime"""
        dt = dt or datetime.now()
        return dt.strftime("%Y-%m")
    
    def _get_day_key(self, dt: Optional[datetime] = None) -> str:
        """Get YYYY-MM-DD key for a datetime"""
        dt = dt or datetime.now()
        return dt.strftime("%Y-%m-%d")
    
    def _get_log_file(self, day_key: str) -> Path:
        """Get path to daily log file"""
        return self.data_dir / f"api_calls_{day_key}.json"
    
    def _get_monthly_summary_file(self, month_key: str) -> Path:
        """Get path to monthly summary file"""
        return self.data_dir / f"monthly_summary_{month_key}.json"
    
    def _load_current_month_cache(self):
        """Load current month's API call counts into memory"""
        month_key = self._get_month_key()
        summary_file = self._get_monthly_summary_file(month_key)
        
        if summary_file.exists():
            with open(summary_file, 'r') as f:
                data = json.load(f)
                self._monthly_cache = defaultdict(int, data.get("api_counts", {}))
    
    def _save_monthly_summary(self):
        """Save current month's summary to file"""
        month_key = self._get_month_key()
        summary_file = self._get_monthly_summary_file(month_key)
        
        summary = {
            "month": month_key,
            "api_counts": dict(self._monthly_cache),
            "costs": self.calculate_monthly_costs(),
            "last_updated": datetime.now().isoformat()
        }
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
    
    def log_api_call(
        self,
        api_type: str,
        endpoint: str = "",
        request_count: int = 1,
        details: Optional[Dict] = None
    ) -> APICallLog:
        """
        Log an API call. Call this every time you make a Google API request.
        
        Args:
            api_type: One of the keys from GOOGLE_PLACES_PRICING (e.g., "text_search_pro")
            endpoint: The specific endpoint called (for debugging)
            request_count: Number of requests (usually 1)
            details: Optional dict with additional context
        
        Returns:
            APICallLog record
        
        Example:
            tracker.log_api_call("text_search_pro", "/v1/places:searchText", details={"query": "restaurants"})
        """
        with self._lock:
            now = datetime.now()
            day_key = self._get_day_key(now)
            
            # Calculate estimated cost for this call
            estimated_cost = self._calculate_call_cost(api_type, request_count)
            
            # Create log entry
            log_entry = APICallLog(
                timestamp=now.isoformat(),
                api_type=api_type,
                endpoint=endpoint,
                request_count=request_count,
                estimated_cost=estimated_cost,
                details=details
            )
            
            # Update monthly cache
            self._monthly_cache[api_type] += request_count
            
            # Append to daily log file
            log_file = self._get_log_file(day_key)
            logs = []
            if log_file.exists():
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            
            logs.append(log_entry.to_dict())
            
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)
            
            # Update monthly summary
            self._save_monthly_summary()
            
            return log_entry
    
    def _calculate_call_cost(self, api_type: str, request_count: int) -> float:
        """
        Calculate cost for a specific API call, considering free tier.
        Returns estimated cost (may be 0 if within free tier).
        """
        if api_type not in GOOGLE_PLACES_PRICING:
            return 0.0
        
        pricing = GOOGLE_PLACES_PRICING[api_type]
        current_count = self._monthly_cache[api_type]
        new_total = current_count + request_count
        
        # Calculate how many requests are billable (after free cap)
        billable_before = max(0, current_count - pricing["free_cap"])
        billable_after = max(0, new_total - pricing["free_cap"])
        new_billable = billable_after - billable_before
        
        if new_billable <= 0:
            return 0.0
        
        return (new_billable / 1000) * pricing["cost_per_1000"]
    
    def calculate_monthly_costs(self, month_key: Optional[str] = None) -> Dict:
        """
        Calculate total costs for a month, broken down by API type.
        
        Returns dict with:
            - total_requests: Total API calls made
            - free_requests: Requests covered by free tier
            - billable_requests: Requests that incur cost
            - gross_cost: Cost before $200 credit
            - credit_applied: Credit amount used
            - net_cost: Final cost after credit
            - by_api: Breakdown per API type
        """
        month_key = month_key or self._get_month_key()
        
        # Load data for the month
        if month_key == self._get_month_key():
            api_counts = dict(self._monthly_cache)
        else:
            summary_file = self._get_monthly_summary_file(month_key)
            if summary_file.exists():
                with open(summary_file, 'r') as f:
                    api_counts = json.load(f).get("api_counts", {})
            else:
                api_counts = {}
        
        result = {
            "month": month_key,
            "total_requests": 0,
            "free_requests": 0,
            "billable_requests": 0,
            "gross_cost": 0.0,
            "credit_applied": 0.0,
            "net_cost": 0.0,
            "by_api": {}
        }
        
        for api_type, count in api_counts.items():
            if api_type not in GOOGLE_PLACES_PRICING:
                continue
            
            pricing = GOOGLE_PLACES_PRICING[api_type]
            free_used = min(count, pricing["free_cap"])
            billable = max(0, count - pricing["free_cap"])
            cost = (billable / 1000) * pricing["cost_per_1000"]
            
            result["total_requests"] += count
            result["free_requests"] += free_used
            result["billable_requests"] += billable
            result["gross_cost"] += cost
            
            result["by_api"][api_type] = {
                "total_calls": count,
                "free_cap": pricing["free_cap"],
                "free_used": free_used,
                "free_remaining": max(0, pricing["free_cap"] - count),
                "billable_calls": billable,
                "cost": round(cost, 4),
                "tier": pricing["tier"]
            }
        
        # Apply $200 credit
        result["credit_applied"] = min(result["gross_cost"], GOOGLE_MONTHLY_CREDIT)
        result["net_cost"] = max(0, result["gross_cost"] - GOOGLE_MONTHLY_CREDIT)
        
        # Round final values
        result["gross_cost"] = round(result["gross_cost"], 2)
        result["credit_applied"] = round(result["credit_applied"], 2)
        result["net_cost"] = round(result["net_cost"], 2)
        
        return result
    
    def get_daily_summary(self, day_key: Optional[str] = None) -> Dict:
        """Get summary for a specific day"""
        day_key = day_key or self._get_day_key()
        log_file = self._get_log_file(day_key)
        
        if not log_file.exists():
            return {"date": day_key, "total_calls": 0, "total_cost": 0, "by_api": {}}
        
        with open(log_file, 'r') as f:
            logs = json.load(f)
        
        summary = {
            "date": day_key,
            "total_calls": 0,
            "total_cost": 0.0,
            "by_api": defaultdict(lambda: {"calls": 0, "cost": 0.0})
        }
        
        for log in logs:
            summary["total_calls"] += log["request_count"]
            summary["total_cost"] += log["estimated_cost"]
            summary["by_api"][log["api_type"]]["calls"] += log["request_count"]
            summary["by_api"][log["api_type"]]["cost"] += log["estimated_cost"]
        
        summary["by_api"] = dict(summary["by_api"])
        summary["total_cost"] = round(summary["total_cost"], 4)
        
        return summary
    
    def get_budget_status(self) -> Dict:
        """
        Get current budget status with alerts.
        
        Returns:
            status: "healthy", "warning", or "critical"
            details per API with usage percentages
        """
        monthly = self.calculate_monthly_costs()
        
        # Check overall budget (gross cost vs $200 credit)
        credit_usage_pct = monthly["gross_cost"] / GOOGLE_MONTHLY_CREDIT if GOOGLE_MONTHLY_CREDIT > 0 else 0
        
        if credit_usage_pct >= ALERT_THRESHOLDS["critical"]:
            overall_status = "critical"
        elif credit_usage_pct >= ALERT_THRESHOLDS["warning"]:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        # Check individual API free tier usage
        api_alerts = []
        for api_type, data in monthly["by_api"].items():
            if data["free_cap"] == float('inf'):
                continue
            
            usage_pct = data["total_calls"] / data["free_cap"]
            if usage_pct >= ALERT_THRESHOLDS["critical"]:
                api_alerts.append({
                    "api": api_type,
                    "status": "critical",
                    "usage_pct": round(usage_pct * 100, 1),
                    "message": f"{api_type}: {data['total_calls']:,}/{data['free_cap']:,} calls ({usage_pct*100:.1f}%)"
                })
            elif usage_pct >= ALERT_THRESHOLDS["warning"]:
                api_alerts.append({
                    "api": api_type,
                    "status": "warning",
                    "usage_pct": round(usage_pct * 100, 1),
                    "message": f"{api_type}: {data['total_calls']:,}/{data['free_cap']:,} calls ({usage_pct*100:.1f}%)"
                })
        
        return {
            "overall_status": overall_status,
            "credit_usage_pct": round(credit_usage_pct * 100, 1),
            "credit_remaining": round(GOOGLE_MONTHLY_CREDIT - monthly["gross_cost"], 2),
            "api_alerts": api_alerts,
            "monthly_summary": monthly
        }
    
    def get_static_costs(self) -> Dict:
        """Get static/fixed costs"""
        annual_total = sum(
            c["cost"] for c in STATIC_COSTS.values() 
            if c["frequency"] == "annual"
        )
        monthly_total = sum(
            c["cost"] for c in STATIC_COSTS.values() 
            if c["frequency"] == "monthly"
        )
        
        return {
            "static_costs": STATIC_COSTS,
            "annual_total": annual_total,
            "monthly_total": monthly_total,
            "monthly_amortized": round(annual_total / 12 + monthly_total, 2)
        }
    
    def get_recent_calls(self, limit: int = 20) -> List[Dict]:
        """
        Get recent API calls from today's log.

        Args:
            limit: Maximum number of calls to return (default 20)

        Returns:
            List of recent API call records, newest first
        """
        day_key = self._get_day_key()
        log_file = self._get_log_file(day_key)

        if not log_file.exists():
            return []

        with open(log_file, 'r') as f:
            logs = json.load(f)

        # Return most recent calls first
        return logs[-limit:][::-1]

    def get_full_report(self) -> Dict:
        """Get complete cost report for dashboard"""
        monthly = self.calculate_monthly_costs()
        budget = self.get_budget_status()
        static = self.get_static_costs()
        today = self.get_daily_summary()

        return {
            "generated_at": datetime.now().isoformat(),
            "budget_status": budget,
            "monthly_dynamic_costs": monthly,
            "static_costs": static,
            "today": today,
            "total_monthly_cost": round(
                monthly["net_cost"] + static["monthly_amortized"], 2
            )
        }


# ============================================
# Flask Blueprint for API endpoints
# ============================================

def create_cost_tracker_blueprint(tracker: CostTracker):
    """
    Create Flask blueprint with cost tracking endpoints.
    
    Usage in your Flask app:
        from cost_tracker import CostTracker, create_cost_tracker_blueprint
        
        tracker = CostTracker()
        app.register_blueprint(create_cost_tracker_blueprint(tracker), url_prefix='/api/costs')
    """
    from flask import Blueprint, jsonify, request
    
    bp = Blueprint('cost_tracker', __name__)
    
    @bp.route('/report', methods=['GET'])
    def get_report():
        """Get full cost report"""
        return jsonify(tracker.get_full_report())
    
    @bp.route('/monthly', methods=['GET'])
    def get_monthly():
        """Get monthly costs. Optional: ?month=YYYY-MM"""
        month = request.args.get('month')
        return jsonify(tracker.calculate_monthly_costs(month))
    
    @bp.route('/daily', methods=['GET'])
    def get_daily():
        """Get daily summary. Optional: ?date=YYYY-MM-DD"""
        day = request.args.get('date')
        return jsonify(tracker.get_daily_summary(day))
    
    @bp.route('/budget', methods=['GET'])
    def get_budget():
        """Get budget status with alerts"""
        return jsonify(tracker.get_budget_status())
    
    @bp.route('/static', methods=['GET'])
    def get_static():
        """Get static costs"""
        return jsonify(tracker.get_static_costs())
    
    @bp.route('/pricing', methods=['GET'])
    def get_pricing():
        """Get current pricing configuration"""
        return jsonify({
            "google_places": GOOGLE_PLACES_PRICING,
            "static_costs": STATIC_COSTS,
            "monthly_credit": GOOGLE_MONTHLY_CREDIT,
            "alert_thresholds": ALERT_THRESHOLDS
        })

    @bp.route('/recent', methods=['GET'])
    def get_recent():
        """Get recent API calls. Optional: ?limit=N (default 20)"""
        limit = request.args.get('limit', 20, type=int)
        return jsonify(tracker.get_recent_calls(limit))

    return bp


# ============================================
# Decorator for easy integration
# ============================================

def track_api_call(tracker: CostTracker, api_type: str):
    """
    Decorator to automatically track API calls.
    
    Usage:
        @track_api_call(tracker, "text_search_pro")
        def search_restaurants(query):
            # Your Google Places API call here
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            tracker.log_api_call(
                api_type=api_type,
                endpoint=func.__name__,
                details={"args": str(args)[:100], "kwargs": str(kwargs)[:100]}
            )
            return result
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator


# ============================================
# CLI for testing
# ============================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Hopwise Cost Tracker CLI")
    parser.add_argument("command", choices=["report", "monthly", "daily", "budget", "test"])
    parser.add_argument("--month", help="Month in YYYY-MM format")
    parser.add_argument("--date", help="Date in YYYY-MM-DD format")
    
    args = parser.parse_args()
    
    tracker = CostTracker()
    
    if args.command == "report":
        print(json.dumps(tracker.get_full_report(), indent=2))
    elif args.command == "monthly":
        print(json.dumps(tracker.calculate_monthly_costs(args.month), indent=2))
    elif args.command == "daily":
        print(json.dumps(tracker.get_daily_summary(args.date), indent=2))
    elif args.command == "budget":
        print(json.dumps(tracker.get_budget_status(), indent=2))
    elif args.command == "test":
        # Simulate some API calls for testing
        print("Simulating API calls...")
        tracker.log_api_call("text_search_pro", "/v1/places:searchText", details={"query": "restaurants near me"})
        tracker.log_api_call("place_details_pro", "/v1/places/ChIJ...", details={"place_id": "ChIJ..."})
        tracker.log_api_call("autocomplete", "/v1/places:autocomplete", request_count=5)
        print("Done! Run 'report' to see results.")
        print(json.dumps(tracker.get_full_report(), indent=2))
