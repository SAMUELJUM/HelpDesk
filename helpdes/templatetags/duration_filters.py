from datetime import datetime, timedelta
from django.utils import timezone
from django.http import QueryDict
from django import template

register = template.Library()

@register.filter
def format_timedelta(value):
    if not value:
        return "N/A"
    total_seconds = int(value.total_seconds())
    days = value.days
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{days}d {hours % 24}h {minutes}m"


class DurationFilter:
    def __init__(self, period='12m', custom_start=None, custom_end=None):
        self.period = period
        self.custom_start = custom_start
        self.custom_end = custom_end
        self.date_range = self._calculate_date_range()

    def _calculate_date_range(self):
        now = timezone.now()

        if self.period == '1m':
            start_date = now - timedelta(days=30)
        elif self.period == '3m':
            start_date = now - timedelta(days=90)
        elif self.period == '6m':
            start_date = now - timedelta(days=180)
        elif self.period == '12m':
            start_date = now - timedelta(days=365)
        elif self.period == 'custom' and self.custom_start and self.custom_end:
            try:
                start_date = datetime.strptime(self.custom_start, '%Y-%m-%d').date()
                end_date = datetime.strptime(self.custom_end, '%Y-%m-%d').date()
                return (start_date, end_date)
            except ValueError:
                pass  # Fall through to default

        # Default to last 12 months
        start_date = now - timedelta(days=365)
        return (start_date, now.date())

    @classmethod
    def from_request(cls, request):
        if request.method == 'GET':
            data = request.GET
        else:
            data = QueryDict()

        return cls(
            period=data.get('period', '12m'),
            custom_start=data.get('start_date'),
            custom_end=data.get('end_date')
        )


def get_default_duration():
    """Returns default duration filter (last 12 months)"""
    return DurationFilter(period='12m')