#! /usr/bin/env python
#
# Mixpanel, Inc. -- http://mixpanel.com/
#
# Python API client library to consume mixpanel.com analytics data.

import urllib
import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings

try:
    import json
except ImportError:
    import simplejson as json


class Mixpanel(object):

    ENDPOINT = 'https://mixpanel.com/api'
    VERSION = '2.0'

    def __init__(self, api_secret):
        self.api_secret = api_secret

    def request(self, methods, params, http_method='GET', format='json'):
        """
            methods - List of methods to be joined, e.g. ['events', 'properties', 'values']
                      will give us http://mixpanel.com/api/2.0/events/properties/values/
            params - Extra parameters associated with method
        """
        params['format'] = format

        request_url = '/'.join([self.ENDPOINT, str(self.VERSION)] + methods)
        if http_method == 'GET':
            data = None
            request_url = request_url + '/?' + self.unicode_urlencode(params)
        else:
            data = self.unicode_urlencode(params)

        response = requests.get(url=request_url, auth=HTTPBasicAuth(self.api_secret, ''))
        return json.loads(response.content)

    def unicode_urlencode(self, params):
        """
            Convert lists to JSON encoded strings, and correctly handle any
            unicode URL parameters.
        """
        if isinstance(params, dict):
            params = params.items()
        for i, param in enumerate(params):
            if isinstance(param[1], list):
                params[i] = (param[0], json.dumps(param[1]),)

        return urllib.urlencode(
            [(k, isinstance(v, unicode) and v.encode('utf-8') or v) for k, v in params]
        )

if __name__ == '__main__':
    api = Mixpanel(settings.MIXPANEL_SECRET_KEY)
    data = api.request(['events'], {
        'event': ['pages'],
        'unit': 'hour',
        'interval': 24,
        'type': 'general'
    })
    print data
