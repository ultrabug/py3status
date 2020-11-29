"""
Displays result of a Prometheus query.

Configuration parameters:
    color: Text colour. Supports py3status colour names.
        Examples: GOOD, DEGRADED, BAD, #E9967A
        (default None)
    format: Formatting of query result. Can refer to all labels from the query
        result. Query value placeholder __v.
        (default "{__v:.0f}")
    join: If query returned multiple rows, join them using this string.
        If you want to show just one, update your query.
        (default None)
    query: The PromQL query
        (default None)
    query_interval: Re-query interval in seconds.
        (default 60)
    server: str, URL pointing at your Prometheus(-compatible) server, example:
        http://prom.int.mydomain.net:9090
        (default None)
    units: Dict with py3.format_units arguments, if you want human-readable
        unit formatting. Example: {"unit": "Wh", "si": True}
        If used, __v placeholder will contain formatted output. __n and __u
        will contain number and unit separately if you want to more finely
        control formatting.
        (default None)

Dynamic format placeholders:
    All query result labels are available as format placeholders. The vector
    values themselves are in placeholder __v. (Or __n and __u if you specified
    units).

Examples:
    # If blackbox exporter ran into any failures, show it. If everything
    # is healthy this will produce 0 rows hence not shown.
    query = "probe_success == 0"
    format = "💀 {job} {instance} 💀"
    color = "bad"

    # Basic Prometheus stat
    query = "sum(prometheus_sd_discovered_targets)"
    format = "{__v:.0f} targets monitored"
    color = "ok"

@author github.com/Wilm0r

SAMPLE OUTPUT
{"full_text": "Ceph 21% (944GiB/4.4TiB)", "instance": "", "name": "prometheus"}
"""


class Py3status:
    # available configuration parameters
    color = None
    format = "{__v:.0f}"
    join = None
    query = None
    query_interval = 60
    server = None
    units = None

    def prometheus(self):
        self._rows = []
        self._rownum = 0
        rows = self._query(self.query)
        res = []
        for row in rows:
            val = float(row["value"][1])
            if self.units:
                num, unit = self.py3.format_units(val, **self.units)
                val = f"{num}{unit}"
            else:
                num = val
                unit = None

            vars = dict(row["metric"])
            vars.update({"__v": val, "__n": num, "__u": unit})
            res.append(self.format.format(**vars))

        if res:
            join = self.join or ""
            res = join.join(res)
        else:
            res = ""

        ret = dict(full_text=res, cached_until=self.py3.time_in(self.query_interval))
        if self.color:
            if self.color.startswith("#"):
                ret["color"] = self.color
            else:
                entry = "COLOR_" + self.color.upper()
                if getattr(self.py3, entry):
                    ret["color"] = getattr(self.py3, entry)
        return ret

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
