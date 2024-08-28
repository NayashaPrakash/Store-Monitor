import tempfile
from .models import StoreStatus,  ReportStatus , StoreStatusLog , StoreReport , Store
from django.utils import timezone
from pytz import timezone as pytz_timezone
import datetime
import csv
import os

def trigger_report_combined(report):
    stores = Store.objects.all()[:200]
    csv_data = [generate_report_data(store) for store in stores]
    generate_csv_file(report, csv_data)
    return report

def generate_report_data(store):
    tz = store.timezone_str or 'America/Chicago'
    target_timezone = pytz_timezone(tz)

    latest_log = StoreStatusLog.objects.order_by('-timestamp').first()
    if not latest_log:
        return [store.pk] + [0] * 6 + ["minutes"] * 6  # Default data if no logs are present

    local_time = latest_log.timestamp.astimezone(target_timezone)
    utc_time = latest_log.timestamp.astimezone(pytz_timezone('UTC'))
    current_day = local_time.weekday()
    current_time = local_time.time()

    last_one_hour_data = get_uptime_downtime_data(store, utc_time, current_day, current_time, period='hour')
    last_one_day_data = get_uptime_downtime_data(store, utc_time, current_day, current_time, period='day')
    last_one_week_data = get_uptime_downtime_data(store, utc_time, current_day, current_time, period='week')

    return [
        store.pk,
        last_one_hour_data["uptime"], last_one_hour_data["downtime"],
        last_one_day_data["uptime"], last_one_day_data["downtime"],
        last_one_week_data["uptime"], last_one_week_data["downtime"]
    ]

def generate_csv_file(report, csv_data):
    with tempfile.TemporaryDirectory() as temp_dir:
        file_name = f"{report.pk}.csv"
        temp_file_path = os.path.join(temp_dir, file_name)

        with open(temp_file_path, "w", newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(["store_id", "last_hour_uptime (min)", "last_hour_downtime (min)", "last_day_uptime (hrs)", "last_day_downtime (hrs)", "last_week_uptime(hrs)", "last_week_downtime (hrs)"])
            for data in csv_data:
                csv_writer.writerow(data)
                print(data)

        report.report_url.save(file_name, open(temp_file_path, "rb"))
        report.status = ReportStatus.COMPLETED
        report.save()

def get_uptime_downtime_data(store, utc_time, current_day, current_time, period):
    data = {"uptime": 0, "downtime": 0}
    time_deltas = {
        'hour': datetime.timedelta(hours=1),
        'day': datetime.timedelta(days=1),
        'week': datetime.timedelta(days=7)
    }
    period_ago = utc_time - time_deltas[period]

    if period == 'hour':
        unit = 'minutes'
    else:
        unit = 'hours'

    is_store_open = store.timings.filter(
        day__gte=current_day - (7 if period == 'week' else 1),
        day__lte=current_day,
        start_time__lte=current_time,
        end_time__gte=current_time
    ).exists()

    if not is_store_open:
        return data

    logs = store.status_logs.filter(timestamp__gte=period_ago).order_by('timestamp')
    if not logs.exists():
        return data

    if period == 'hour':
        timestamps = [log.timestamp for log in logs]
        statuses = [log.status == StoreStatus.ACTIVE for log in logs]
        time_intervals = [(timestamps[i+1] - timestamps[i]).total_seconds() / 60 for i in range(len(timestamps) - 1)]

        data["uptime"] = sum(time_intervals[i] for i in range(len(statuses) - 1) if statuses[i])
        data["downtime"] = sum(time_intervals[i] for i in range(len(statuses) - 1) if not statuses[i])

    else:
        total_minutes = 0
        for log in logs:
            if store.timings.filter(day=log.timestamp.weekday(), start_time__lte=log.timestamp.time(), end_time__gte=log.timestamp.time()).exists():
                total_minutes += 1 if log.status == StoreStatus.ACTIVE else 0

        data["uptime"] = total_minutes / 60
        data["downtime"] = (24 * (1 if period == 'day' else 7)) - data["uptime"]

    data["unit"] = unit
    return data
