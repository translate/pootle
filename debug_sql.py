from django.db import connection
from django.utils.log import getLogger

logger = getLogger(__name__)

class QueryCountDebugMiddleware(object):
    """
    This middleware will log the number of queries run
    and the total time taken for each request (with a
    status code of 200). It does not currently support
    multi-db setups.
    """
    def process_request(self, request):
        self.start = len(connection.queries)

    def process_response(self, request, response):
        if response.status_code == 200:
            total_time = 0
            for query in connection.queries:
                print
                print query                
                query_time = query.get('time')
                if query_time is None:
                    query_time = query.get('duration', 0) / 1000
                total_time += float(query_time)
            logger.debug('%s queries run, total %s seconds' % (len(connection.queries), total_time))
            print('%s queries run, total %s seconds' % (len(connection.queries), total_time))
        import json
        try:
            content = json.loads(response.content)
            content["queries"] = connection.queries
            response.content = json.dumps(content)
        except:
            pass
        return response
