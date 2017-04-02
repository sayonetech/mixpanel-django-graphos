import datetime

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth.models import User
from dateutil.parser import parse

from mixpanel_django_graphos.mixpanel import Mixpanel


@csrf_exempt
def get_user_report(request):
    """
    :param request:
    :return: Event data from mixpanel
    """
    user_id = request.GET.get('user')

    # Connect to Mixpanel
    if settings.MIXPANEL_API_KEY and settings.MIXPANEL_SECRET_KEY:
        api = Mixpanel(api_secret=settings.MIXPANEL_SECRET_KEY)
    else:
        return HttpResponse('Mixpanel is not setup', status=500)

    params = {}
    params['event'] = request.GET.get('event')
    if request.GET.get('limit'):
        params['limit'] = request.GET.get('limit')

    # Generate query to extract events
    to_date = datetime.datetime.now()
    from_date = datetime.date(year=to_date.year, month=to_date.month, day=1)

    if request.GET.get('startdate') and request.GET.get('enddate'):
        # If a date range is provided in query parameters, use it.
        start_date = parse(request.GET.get('startdate')).strftime('%Y-%m-%d')
        end_date = parse(request.GET.get('enddate'))

        if end_date > datetime.datetime.now():
            end_date = datetime.datetime.now()
        end_date = end_date.strftime('%Y-%m-%d')

        params.update({
            'from_date': start_date,
            'to_date': end_date
        })
    else:
        # Filter events generated in the current month
        params.update({
            'from_date': from_date.strftime('%Y-%m-%d'),
            'to_date': to_date.strftime('%Y-%m-%d'),
        })

    # Filter by user if it's defined
    if user_id != 'all_users':
        user = get_object_or_404(User, id=user_id)
        params['where'] = 'properties["user_id"]=={}'.format(user.pk)

    # Do not filter by event if 'all' param was passed
    if request.GET.get('all'):
        del params['event']

    methods = ['segmentation']

    # Retrieve from MixPanel
    mp_data = api.request(methods, params)
    data_records = {
        'mp_activity_data': mp_data
    }

    if request.GET.get('top'):
        params['on'] = request.GET.get('top')
        top_mp_data = api.request(methods, params)
        data_records['top_mp_data'] = top_mp_data

    return data_records
