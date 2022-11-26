import datetime


def timestamp_to_utc(timestamp):
    """timestamp -> utc time
    print(timestamp_to_utc('1576022400'))"""
    return datetime.datetime.utcfromtimestamp(int(timestamp))


def utc_to_timestamp(utc_time):
    """utc_time -> timestamp
    print(utc_to_timestamp('2019-12-11 00:00:00'))"""
    return int(
        datetime.datetime.strptime(utc_time, "%Y-%m-%d %H:%M:%S").replace(tzinfo=datetime.timezone.utc).timestamp()
    )


def seconds_in_day(datetime):
    return datetime.hour * 3600 + datetime.minute * 60 + datetime.second
