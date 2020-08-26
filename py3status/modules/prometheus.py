#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Displays result of a Prometheus query.

Configuration parameters:
    server: str, URL pointing at your Prometheus(-compatible) server, example:
        http://prom.int.mydomain.net:9090
    query: PromQL Query
    query_interval: Re-query interval in seconds. (default 60)
    format: Formatting of query result. Can refer to all labels from the query
        result. Query value placeholder __v.
    units: Dict with py3.format_units arguments, if you want human-readable
        unit formatting. Example: {"unit": "Wh", "si": True}
        If used, __v placeholder will contain formatted output. __n and __u
        will contain number and unit separately if you want to more finely
        control formatting.
    color: Text colour. Supports py3status colour names.
        Examples: ok, bad, #E9967A
    join: If query returned multiple rows, join them using this string. If you
        want to show just one, update your query.

For example:
    # If blackbox exporter ran into any failures, show it. If everything
    # is healthy this will produce 0 rows hence not shown.
    query = "probe_success == 0"
    format = "💀 %(job)s %(instance)s 💀"
    color = "bad"

    # Basic Prometheus stat
    query = "sum(prometheus_sd_discovered_targets)"
    format = "%(__v)d targets monitored"
    color = "ok"
"""


class Py3status:
    server = None
    query = None
    format = "%(__v)f"
    units = None
    color = "ok"
    join = None

    query_interval = 90

    def prometheus(self):
        self._rows = []
        self._rownum = 0
        rows = self._query(self.query)
        res = []
        for row in rows:
            val = float(row["value"][1])
            if self.units:
                num, unit = self.py3.format_units(val, **self.units)
                val = "%s%s" % (num, unit)
            else:
                num = val
                unit = None

            vars = dict(row["metric"])
            vars.update({
                "__v": val,
                "__n": num,
                "__u": unit,
            })
            res.append(self.format % vars)
        
        if res:
            join = self.join or ""
            res = join.join(res)
        else:
            res = ""

        return dict(
            full_text=res,
            color=self.color,
            cached_until=self.py3.time_in(self.query_interval),
        )

    def _query(self, query):
        r = self.py3.request(self.server + "/api/v1/query", params={"query": query})
        if r.status_code != 200:
            return []
        r = r.json()
        if r["status"] != "success" or r["data"]["resultType"] != "vector":
            return []
        return r["data"]["result"]


if __name__ == "__main__":
    from py3status.module_test import module_test
    module_test(Py3status)
