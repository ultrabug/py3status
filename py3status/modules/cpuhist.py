import itertools

class Py3status:
  cpu_data = {}
  cache_timeout = 1
  thresholds = [
    (0.0, "good"),
    (0.6, "degraded"),
    (0.8, "bad"),
  ]

  def cpustats(self):
    with open('/proc/stat', 'r') as stat_file:
      lines = stat_file.readlines()
    cpu_lines = itertools.islice((l for l in lines if l.startswith('cpu')), 1, None)
    next_cpu_data = {id: (busy, total) for id, busy, total in (Py3status._calc(l) for l in cpu_lines)}
    calc = next_cpu_data.copy()
    for id, (busy, total) in self.cpu_data.items():
      next_busy, next_total = calc.get(id)
      calc[id] = (next_busy - busy, next_total - total)
    self.cpu_data = next_cpu_data
    to_print = (Py3status._display(busy / total) for id, (busy, total) in calc.items())
    avg = sum(busy / total for id, (busy, total) in calc.items()) / len(calc)

    return {
      'full_text': f"cpu hist: {''.join(to_print)}",
      'cached_until': self.py3.time_in(self.cache_timeout),
      'color': self.py3.threshold_get_color(avg)
    }

  def _calc(line):
    split = line.split(' ')
    id = split[0]
    total = sum(int(x) for x in split[1:])
    busy = total - int(split[4]) # subtract idle time

    return id, busy, total

  def _display(pct):
    if pct > 0.8:
      return '⡇'
    if pct > 0.6:
      return '⡆'
    if pct > 0.4:
      return '⡄'
    if pct > 0.2:
      return '⡀'
    return '⠀'
