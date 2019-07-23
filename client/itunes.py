import json
import logging
from enum import Enum

import requests


class Method:
    _method = ""
    _count = 0
    _m_type = "GET"

    def __init__(self, *args):
        assert self._count == len(args)
        self.path_args = args

    def get_endpoint(self, schema, host, port):
        sh = f"{schema}://{host}{port}"
        endpoint = requests.utils.requote_uri(f"/{self._method}") % self.path_args
        return "{}{}".format(sh, endpoint)

    @property
    def m_type(self):
        return self._m_type

    @staticmethod
    def response_process(resp, *args):
        return resp, STATUSES.OK


class GetAppsPage(Method):
    _method = 'us/genre/id%s/'
    _m_type = "GET"
    _count = 1


class STATUSES(Enum):
    FAIL = 0
    OK = 1


class ITunesClient:
    def __init__(self, schema='', host='', port=''):
        self.host = host
        if host is not None:
            self.host = host
        self.port = ''
        if port is not None:
            self.port = port

        self.headers = {"Content-Type": "application/json"}
        self.schema = schema

        # TODO: add healthz check

    def request(self, method, params=None, headers=None, body=None):
        try:
            endpoint = method.get_endpoint(self.schema, self.host, self.port)

            if headers is None:
                headers = self.headers

            m_type = method.m_type
            if m_type == 'GET':
                assert body is None, 'For GET method body must be empty'
                r = requests.get(url=endpoint, params=params, headers=headers)
            elif m_type == 'POST':
                r = requests.post(url=endpoint, params=params, data=json.dumps(body), headers=headers)
            else:
                raise Exception("\nnot implemented method request: %s" % method.m_type)

            if r.status_code // 100 != 2:
                args = (r.status_code, str(r._content), method, body, params, headers)
                logging.error("status code: %d. text: %s. method: %s. body: %s. params: %s. header: %s" % args)
                return {}, STATUSES.FAIL
            return method.response_process(r.text, method, params, headers, body)
        except Exception as e:
            t = (e, method, params, headers, body)
            logging.error("unexpected error: %s. method: %s. params: %s. headers: %s. body: %s" % t)
            return {}, STATUSES.EXCEPTION
