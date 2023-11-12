from datetime import timedelta

LOW_STOCK_LIMIT = 30

TIME_INTERVAL_MAPPING = {
    'daily': timedelta(days=1),
    'weekly': timedelta(weeks=1),
    'monthly': timedelta(days=30),  # Adjust as needed
    'yearly': timedelta(days=365),  # Adjust as needed
}