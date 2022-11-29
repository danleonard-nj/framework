from datetime import datetime


def hours_to_seconds(hours):
    return hours * 60 * 60


def get_utc_now():
    return (datetime
            .utcnow()
            .strftime('%Y-%m-%dT%H:%M:%S'))
