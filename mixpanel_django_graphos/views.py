import datetime

from django.views.generic import TemplateView
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from graphos.sources.simple import SimpleDataSource
from graphos.renderers.gchart import LineChart
from dateutil.parser import parse

from mixpanel_django_graphos import settings
from mixpanel_django_graphos.mixpanel import Mixpanel


def get_or_none(classmodel, **kwargs):
    try:
        return classmodel.objects.get(**kwargs)
    except classmodel.DoesNotExist:
        return None


@csrf_exempt
def get_brand_report(request):
    """
    For admin report. Retrieve data from mixpanel to obtain datas - Total placelet views,
    Total placelet views, etc.
    :param request:
    :return:
    """
    # If brand is defined check if it's valid
    brand_slug = request.GET.get('brand')
    if brand_slug != 'all_brands':
        brand = get_object_or_404(Brand, slug=brand_slug)
        # Check if the user is admin or belong to the brand
        if (not (request.user.is_superuser or
                 not request.user.is_authenticated() or
                 brand in request.user.brands.all() or
                 brand.group in request.user.groups.all())):

            return HttpResponse('Unauthorized', status=401)
    else:
        # Only admin users can retreived reports without brand filter
        if not request.user.is_superuser:
            return HttpResponse('Unauthorized', status=401)

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
    # Filter by brand if it's defined
    if brand_slug != 'all_brands':
        brand = get_object_or_404(Brand, slug=brand_slug)
        params['where'] = 'properties["brand_id"]=={}'.format(brand.pk)

    # Do not filter by event if 'all' param was passed
    if request.GET.get('all'):
        del params['event']

    methods = ['segmentation']

    #checks whether request has param type, to differentiate the request from admin or api
    if request.GET.get('type'):
        params['type'] = request.GET.get('type')
        mp_data = api.request(methods, params)
        data_records = {
            'mp_data': mp_data
        }
    else:
        # Retrieve events from MixPanel - Total Placelet Views (type = general)
        placelet_views = api.request(methods, params)

        # Retrieve events from MixPanel - Total Placelets Loaded (type = unique)
        params['type'] = 'unique'
        placelets_loaded = api.request(methods, params)

        data_records = {
            'placelet_views': placelet_views,
            'placelets_loaded': placelets_loaded
        }
    if request.GET.get('top'):
        params['on'] = request.GET.get('top')
        top_mp_data = api.request(methods, params)
        data_records['top_mp_data'] = top_mp_data

    # placelet_ld_events = ['Placelet Loaded']
    # placelet_ld_data = json.dumps(
    #     list(filter(lambda d: d['event'] in placelet_ld_events, data_records))
    # )
    # print placelet_ld_data, 'placelet_ld_data###'

    return data_records

    # Map and save data into a csv file
    response = HttpResponse(content_type='text/csv')
    writer = unicodecsv.writer(response)
    # Write csv header
    header = ['event'] + REPORT_FIELDS
    writer.writerow(tuple(header))
    # Write csv content
    writer.writerows(map(map_mixpanel_event, data_records))

    return response


class ReportAggregateActivityView2(TemplateView):
    template_name = 'admin/backend/reports/reports.html'

    def get_context_data(self, *args, **kwargs):
        context = super(ReportAggregateActivityView2, self).get_context_data(*args, **kwargs)
        # req = requests.get('https://0d1f2b8b4539fd6452ec08402c4a44ef@mixpanel.com/api/2.0/events/names?type=general')
        # context['event_names'] = json.loads(req.content)
        context['brands'] = Brand.objects.all()
        context['fiz_provider'] = get_or_none(Provider, name=Provider.FIZ)
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        brand_slug = request.GET.get('brand')
        if brand_slug:
            data_records = get_brand_report(request)

            context['placelet_views_chart'] = self.get_segmentation_data(
                'placelet_views', data_records)
            context['placelets_loaded_chart'] = self.get_segmentation_data(
                'placelets_loaded', data_records)

        return self.render_to_response(context)

    def get_segmentation_data(self, key, data_records):
        if not key:
            return
        x_axis_label = 'Date'
        y_axis_label = None
        if key == 'placelet_views':
            y_axis_label = 'Total Placelet Views'
        elif key == 'placelets_loaded':
            y_axis_label = 'Placelets Loaded'
        data = [
            [x_axis_label, y_axis_label]
        ]
        segmentation_data = data_records[key]["data"]["values"]
        if segmentation_data:
            chart_data = segmentation_data["Placelet Loaded"]
            for key, value in chart_data.iteritems():
                temp = [key, value]
                data.append(temp)

        return self.load_chart_data(data)

    def load_chart_data(self, data):
        # DataSource object
        data_source = SimpleDataSource(data=data)
        # Chart object
        chart = LineChart(data_source)
        return chart
