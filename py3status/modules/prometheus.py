#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Displays results of configured Prometheus queries.

Configuration parameters:
    server: str, URL pointing at your Prometheus(-compatible) server, example:
        http://prom.int.mydomain.net:9090
    fields: list of dicts, explained below
    query_interval: Re-query interval in seconds. (default 60)
    rotate_interval: To rotate through configured fields, set this to the
        number of seconds you want each of them to show up. (default 8, set
        to 0 to disable rotation.)
    reset_delay: After manual scrolling through fields, resume rotation/
        reset to first field after this number of seconds. (default 60)

Field configuration: List of dicts, each of which having these fields:
    q: Query
    fmt: Formatting of query result. Can refer to all labels from the query
        result. Query value placeholder __v.
    units: Dict with py3.format_units arguments, if you want human-readable
        unit formatting. Example: {"unit": "Wh", "si": True}
        If used, __v placeholder will contain formatted output. __n and __u
        will contain number and unit separately if you want to more finely
        control formatting.
    color: Text colour. Supports py3status colour names.
        Examples: ok, bad, #E9967A
    sub: list of dicts, can be used to merge different queries into a single
        field. Each dict can contain: q, units. When sub is used, query values
        will be in placeholders 0.v, 1.v, ... instead of __v. A field will be
        generated for each unique set of label values returned by all queries.

An example is likely much easier to understand than the above text though:
fields = [
    # If blackbox exporter ran into any failures, show it first. If everything
    # is healthy this will produce 0 fields hence not show up at all.
    {
        "q": "probe_success == 0",
        "fmt": "💀 %(job)s %(instance)s 💀",
        "color": "bad",
    },
    # Ceph cluster utilisation. Note the "> 80" filter at the end of the last
    # query, filtering out any results below 80%. If any query produces no
    # result, no field will get produced, so this field will only show up if
    # your cluster is running out of space.
    {
        "sub": [
            {
                "q": "ceph_cluster_total_used_raw_bytes",
                "units": {"unit": "B", "optimal": 3},
            },
            {
                "q": "ceph_cluster_total_bytes",
                "units": {"unit": "B", "optimal": 3},
            },
            {
                "q": "(ceph_cluster_total_used_raw_bytes / ceph_cluster_total_bytes * 100) > 80",
            },
        ],
        "fmt": "Ceph %(2.v)d%% (%(0.v)s/%(1.v)s)",
        "color": "degraded",
    },
    # Weather info collected by rtl_433 + prometheus exporter. Just convert
    # from m/s to km/h as part of the query expression.
    {
        "sub": [
            {
                "q": "temperature_C{channel='1'}",
            },
            {
                "q": "max_over_time(wind_max_m_s[2m]) * 3.6",
            }
        ],
        "fmt": "🌡️ %(0.v).1f°C 💨 %(1.v)d",
    },
    # Data from a dump1090 (ADS-B air traffic decoder) exporter. I'm
    # monitoring three separate instances, a separate field will get generated
    # for each of them.
    {
        "sub": [
            {
                "q": "num_planes{job='dump1090'}",
            },
            {
                "q": "dist_max{job='dump1090'}",
            },
        ],
        "fmt": "%(location)s ✈️ %(0.v)d (%(1.v)dkm)",
    },
]
"""

import collections
import itertools
import time


class Py3status:
    _rows = []
    _rownum = 0
    _rowid = ()
    _expiry = 0

    server = None
    fields = [
        {
            "q": "sum(prometheus_sd_discovered_targets)",
            "fmt": "%(__v)d targets monitored",
            "color": "ok",
        }
    ]

    query_interval = 90
    rotate_interval = 8
    reset_delay = 60

    _NEVER = 86400000 # 1000d

    def post_config_hook(self):
        now = time.time()
        if self.rotate_interval <= 0:
            self.rotate_interval = self._NEVER
        if self.reset_delay <= 0:
            self.reset_delay = self.rotate_interval
        self._next_reset = now + self._NEVER
        self._next_rotate = now + self.rotate_interval

    def prometheus(self):
        now = time.time()
        if now > self._next_reset:
            self._next_reset = now + self._NEVER
            if self.rotate_interval == self._NEVER:
                self._rotate(-self._rownum)
            else:
                self._next_rotate = 0 # now!
        if now > self._next_rotate:
            self._rotate(1)
            self._next_rotate = now + self.rotate_interval
        if now > self._expiry:
            self._expiry = now + self.query_interval
            self._reload()
        exp = min(self._next_rotate, self._next_reset, self._expiry)
        return {**self._rows[self._rownum][1], **{"cached_until": exp}}

    def _reload(self):
        self._rows = []
        self._rownum = 0
        for part_num, part in enumerate(self.fields):
            res = collections.defaultdict(dict)
            if "sub" in part:
                subs = [{**part, **q} for q in part["sub"]]
            else:
                subs = [part]
            for q_num, sub in enumerate(subs):
                rows = self._query(sub["q"])
                for row in rows:
                    val = float(row["value"][1])
                    if "units" in sub:
                        num, unit = self.py3.format_units(val, **sub["units"])
                        val = "%s%s" % (num, unit)
                    else:
                        num = val
                        unit = None

                    rowid = dict(row["metric"])
                    rowid.pop("__name__", None)
                    rowid = (part_num,) + tuple(sorted(rowid.items()))
                    if len(subs) == 1:
                        prefix = "__"
                    else:
                        prefix = "%d." % q_num
                    res[rowid].update({
                        prefix + "v": val,
                        prefix + "n": num,
                        prefix + "u": unit,
                    })

            new = []
            for rowid, qvals in res.items():
                data = {**qvals , **dict(rowid[1:])}
                try:
                    new.append((rowid, self._format(part, data)))
                except KeyError:
                    pass

            if res and not new:
                # Couldn't join the fields due to complete labels mismatch!
                # Let's guess no join was intended and try again. Just throw
                # all we have together and use that if there's no overlap.
                all = list(itertools.chain(*[list(d.items()) for d in res.values()]))
                if (len(all) == len(dict(all))):
                    try:
                        new.append(((part_num,), self._format(part, dict(all))))
                    except KeyError:
                        pass

            if new and "join" in part:
                joined = []
                for c in new:
                    if joined:
                        joined.append({"full_text": part["join"]})
                    joined.append(c[1])

                new = [(part_num, {"composite": joined})]

            for row in new:
                if self._rowid == row[0]:
                    self._rownum = len(self._rows)
                self._rows.append(row)

    def _query(self, query):
        r = self.py3.request(self.server + "/api/v1/query", params={"query": query})
        if r.status_code != 200:
            return []
        r = r.json()
        if r["status"] != "success" or r["data"]["resultType"] != "vector":
            return []
        return r["data"]["result"]

    def _format(self, part, fields):
        ret = {
            "full_text": part["fmt"] % fields,
        }
        if "color" in part:
            c = part["color"]
            if c.startswith("#"):
                ret["color"] = c
            else:
                entry = "COLOR_" + c.upper()
                if getattr(self.py3, entry):
                    ret["color"] = getattr(self.py3, entry)
        return ret

    def on_click(self, event):
        now = time.time()
        # Feature ideas: left-lick actions? Refresh trigger?
        if event["button"] == 2:   # middle
            self._rotate(-self._rownum)
        elif event["button"] == 4: # scroll up
            self._rotate(-1)
        elif event["button"] == 5: # scroll down
            self._rotate(1)

        self._next_reset = now + self.reset_delay
        self._next_rotate = now + self._NEVER

    def _rotate(self, diff):
        if self._rows:
            self._rownum += diff
            self._rownum %= len(self._rows)
            self._rowid = self._rows[self._rownum][0]


if __name__ == "__main__":
    from py3status.module_test import module_test
    module_test(Py3status)
