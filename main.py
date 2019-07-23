import itertools
import logging
import re

from client.itunes import ITunesClient, GetAppsPage, STATUSES


BadClientStatus = Exception("bad client's status")


def set_config(**kwargs):
    """
    :param kwargs:
    :return:
    """

    logging.basicConfig(
        format='%(asctime)-15s %(levelname)s [%(name)s]: %(message)s',
        filename=kwargs.get('logging_filename', None),
        level=kwargs.get('log_level', logging.INFO),
        filemode='w',
    )


class Scrapper:
    def __init__(self, itunes_client):
        self.client = itunes_client
        self.__it_ids = itertools.chain(
            range(6000, 6026),
            filter(lambda el: el != 7010, range(7000, 7020)),
            (1, 3, 5, 6, 7, 8, 9, 10, 25, 26, 14, 15, 17, 19, 21),
            filter(lambda el: el != 7010, range(7000, 7019)),
            filter(lambda el: el != 13016 and el != 13022, range(13000, 13031)),
        )
        self.__it_letters = itertools.chain(
            (item for item in '0#'),
            map(lambda el: chr(el), range(ord('A'), ord('Z')+1)),
            map(lambda el: chr(el), range(ord('a'), ord('z')+1)),
            map(lambda el: chr(el), range(ord('А'), ord('Я')+1)),
            map(lambda el: chr(el), range(ord('а'), ord('я')+1)),
        )

    @staticmethod
    def __bisect(lo, hi, cond):
        if lo < 0:
            raise ValueError('lo must be non-negative')
        while lo < hi:
            mid = (lo+hi)//2
            if cond(mid):
                lo = mid+1
            else:
                hi = mid
        return lo

    @staticmethod
    def __get_urls(id_, letter, page_number):
        m = GetAppsPage(str(id_))
        params = {
            'letter': letter,
            'page': str(page_number),
        }
        resp, status = client.request(method=m, params=params)
        if status != STATUSES.OK:
            raise BadClientStatus
        regexp = r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?"
        res = re.findall(regexp, resp)
        f = filter(lambda el: el[2].find('/app/') >= 0, res)
        f = filter(lambda el: el[1].find('itunes') < 0, f)
        f = filter(lambda el: el[2].find('/app/id490217893') < 0, f)
        res = list(map(lambda el: f"{el[0]}://{el[1]}{el[2]}", f))
        return res

    def __get_max_page(self, letter, id_, s=1, f=10001):
        return self.__bisect(s, f, lambda page_number: len(self.__get_urls(id_, letter, page_number)) > 0) - 1

    def __iter_pages(self, id_, letter, finish, start=1):
        urls = []
        for p in range(start, finish + 1):
            urls = self.__get_urls(id_, letter, p)
        return urls

    def scrappy_urls(self, start_id=None):
        urls = []
        try:
            for id_ in self.__it_ids:
                if start_id is not None and id_ != start_id:
                    start_id = None
                    continue
                for l in self.__it_letters:
                    logging.info("id=%d. letter=%s" % (id_, l))
                    max_page = self.__get_max_page(letter=l, id_=id_)
                    logging.info("max_page=%d" % max_page)
                    urls += self.__iter_pages(id_=id_, letter=l, finish=max_page)
                    m = GetAppsPage(str(id_))
                    resp, status = client.request(method=m)
                    if status != STATUSES.OK:
                        continue
            return urls
        except Exception as e:
            logging.fatal(e)
            return urls


set_config()
client = ITunesClient(schema='https', host='apps.apple.com')
s = Scrapper(itunes_client=client)
print(s.scrappy_urls())
