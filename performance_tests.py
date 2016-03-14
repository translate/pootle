import time

import requests


BASE_URL = "http://localhost:8000/xhr/units/"
PATHS_FILE = "paths.txt"

PARAMS = [
    "filter=all",
    "filter=all&sort=oldest",
    "filter=incomplete&sort=oldest",
    "filter=translated&sort=oldest",
    "filter=untranslated&sort=oldest"]


class MarkdownTableFormatter(object):

    def __init__(self, path_width=80, param_width=40, timing_width=8):
        self.path_width = path_width
        self.param_width = param_width
        self.timing_width = timing_width

    def format(self, performance_test):
        results = list(
            reversed(
                sorted(
                    performance_test.results,
                    key=lambda res: res[2])))[:20]
        print(
            "|path%s|params%s|timing%s|"
            % ((" " * (self.path_width - 4)),
               (" " * (self.param_width - 6)),
               (" " * (self.timing_width - 6))))
        
        print(
            "|%s|%s|%s|"
            % ("-" * self.path_width,
               "-" * self.param_width,
               "-" * self.timing_width))

        for path, param, timing in results:
            print (
                "|%s%s|%s%s|%s%s|"
                % (path, (" " * (self.path_width - len(path))),
                   param, (" " * (self.param_width - len(param))),
                   timing, (" " * (self.timing_width - len(timing)))))



class GetUnitsPerformance(object):

    def __init__(self, base_url=BASE_URL, paths_file=PATHS_FILE):
        self.base_url = base_url
        self.paths_file = paths_file

    def get_paths(self):
        with open(self.paths_file, "r") as f:
            for line in f.readlines():
                yield line.strip()

    def get_params(self):
        return PARAMS

    @property
    def results(self):
        result = []

        for path in self.get_paths():
            for param in self.get_params():
                start = time.time()
                resp = requests.get(
                    "%s?path=%s&initial=true&%s"
                    % (self.base_url, path, param))
                if not path.endswith("/"):
                    timing = str(
                        sum(float(t["time"])
                            for t
                            in resp.json()["queries"][-2:]))
                else:
                    timing = resp.json()["queries"][-1]["time"]
                result.append(
                    (path,
                     param,
                     timing))
        return result


def run():
    MarkdownTableFormatter().format(GetUnitsPerformance())
