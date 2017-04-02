from django.views.generic import TemplateView

from graphos.sources.simple import SimpleDataSource
from graphos.renderers.gchart import *

from mixpanel_django_graphos.utils import *


class ReportActivityView(TemplateView):
    """
    Retrieve data from Mixpanel, and use graphos to display the data.
    """
    template_name = 'admin/reports.html'

    def get_context_data(self, *args, **kwargs):
        context = super(ReportActivityView, self).get_context_data(*args, **kwargs)
        context['users'] = User.objects.all()
        context['event_names'] = settings.MIXPANEL_EVENT_NAMES
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        user_id = request.GET.get('user')
        if user_id:
            data_records = get_user_report(request)
            context['mp_activity_chart'] = self.get_segmentation_data(
                'mp_activity_data', data_records)

        return self.render_to_response(context)

    def get_segmentation_data(self, key, data_records):
        if not key:
            return
        x_axis_label = 'Date'
        y_axis_label = 'Number of occurrences'
        data = [
            [x_axis_label, y_axis_label]
        ]
        segmentation_data = data_records[key]["data"]["values"]
        if segmentation_data:
            chart_data = segmentation_data[self.request.GET.get('event')]
            for key, value in chart_data.iteritems():
                temp = [key, value]
                data.append(temp)

        return self.load_chart_data(data)

    def load_chart_data(self, data):
        """
        Four among the graphos supported charts are used here.
        :return: Mixpanel data converted to graphos chart display
        """
        # DataSource object
        data_source = SimpleDataSource(data=data)
        # Chart object types
        chart = {
            "piechart": PieChart(data_source),
            "linechart": LineChart(data_source),
            "barchart": BarChart(data_source),
            "columnchart": ColumnChart(data_source)
        }
        return chart
