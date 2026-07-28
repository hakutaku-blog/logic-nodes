import os
import json
import sys
import subprocess

def fetch_yesterday_ga4_stats():
    """GA4 Data APIから昨日のPV数およびユーザー数を取得する"""
    property_id = os.environ.get("GA4_PROPERTY_ID")
    json_credentials = os.environ.get("GA4_SERVICE_ACCOUNT_JSON")

    if not property_id or not json_credentials:
        print("GA4_PROPERTY_ID or GA4_SERVICE_ACCOUNT_JSON not set.")
        return None

    try:
        try:
            from google.analytics.data_v1beta import BetaAnalyticsDataClient
            from google.analytics.data_v1beta.types import DateRange, Metric, RunReportRequest
            from google.oauth2 import service_account
        except ImportError:
            print("Installing google-analytics-data...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "google-analytics-data", "google-auth"])
            from google.analytics.data_v1beta import BetaAnalyticsDataClient
            from google.analytics.data_v1beta.types import DateRange, Metric, RunReportRequest
            from google.oauth2 import service_account

        cred_dict = json.loads(json_credentials)
        credentials = service_account.Credentials.from_service_account_info(cred_dict)
        client = BetaAnalyticsDataClient(credentials=credentials)

        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(start_date="yesterday", end_date="yesterday")],
            metrics=[
                Metric(name="screenPageViews"),
                Metric(name="activeUsers"),
            ],
        )
        response = client.run_report(request)

        if response.rows:
            row = response.rows[0]
            page_views = row.metric_values[0].value
            active_users = row.metric_values[1].value
            return {
                "page_views": int(page_views),
                "active_users": int(active_users)
            }
        else:
            return {
                "page_views": 0,
                "active_users": 0
            }
    except Exception as e:
        print(f"GA4 Stats fetch error: {e}")
        return None
