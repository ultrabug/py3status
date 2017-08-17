import cProfile

# Used in development
enable_profiling = False


def profile(thread_run_fn):
    if not enable_profiling:
        return thread_run_fn

    def wrapper_run(self):
        """Wrap the Thread.run() method
        """
        profiler = cProfile.Profile()
        try:
            return profiler.runcall(thread_run_fn, self)
        finally:
            thread_id = getattr(self, 'ident', 'core')
            profiler.dump_stats("py3status-%s.profile" % thread_id)

    return wrapper_run


class Profiler:
    """
    Helper class to aid profiling.
    We can enable/disable profiling in specific parts of the code as required

    standard cProfile output is sent to /tmp/py3status.prof

    if pyprof2calltree is installed we create kcachegrind profile info
    all files created are in a directory
    /tmp/profile_py3status_<timestamp>_<git branch>

    profiling is enabled via `py3status --profile`
    """

    filename = 'py3status-{name}.prof'
    filename_callgrind = 'callgrind.out.py3status-{name}.prof'
    filename_stats = 'py3status-{name}.stats'
    dir_format = '/tmp/profile_py3status_{timestamp}_{branch}'

    def __init__(self, py3_wrapper):
        # only import stuff if we are profiling
        import os.path
        import subprocess
        from datetime import datetime
        # generate output directory name
        # get git info if we are running in a repo
        try:
            cwd = os.path.dirname(os.path.realpath(__file__))
            branch = subprocess.check_output(
                ['git', 'symbolic-ref', '--short', 'HEAD'], cwd=cwd
            ).decode('utf-8').strip()
        except:
            pass
            branch = ''

        timestamp = datetime.today().strftime('%Y-%m-%d_%H:%M')
        self.output_dir = self.dir_format.format(
            timestamp=timestamp, branch=branch
        )

        self.py3_wrapper = py3_wrapper
        self.running = {}
        self.profilers = {}

    def _profiler(self, name):
        try:
            return self.profilers[name]
        except KeyError:
            pass
        self.profilers[name] = cProfile.Profile()
        return self.profilers[name]

    def enable(self, name=''):
        if self.running.get(name):
            return
        self.running[name] = True
        self._profiler(name).enable()

    def disable(self, name=''):
        self._profiler(name).disable()
        self.running[name] = False

    def exit(self):
        import os
        import pstats
        try:
            from pyprof2calltree import convert
        except ImportError:
            convert = None

        try:
            os.mkdir(self.output_dir)
        except:
            return

        stats_info = {}
        profiles = {}
        streams = []

        for name, p in self.profilers.items():
            if name:
                name = name.split(' ')[0]
            if name not in profiles:
                profiles[name] = []
            profiles[name].append(p)
            if 'full' not in profiles:
                profiles['full'] = []
            profiles['full'].append(p)

        for name, p in profiles.items():
            if not name:
                continue
            filename = self.filename_stats.format(name=name)
            filename = os.path.join(self.output_dir, filename)
            stream = open(filename, 'w')
            streams.append(stream)
            stats_info[name] = pstats.Stats(*p, stream=stream)

        for name, s in stats_info.items():
            filename = self.filename.format(name=name)
            filename = os.path.join(self.output_dir, filename)
            # write profile data
            s.dump_stats(filename)
            s.strip_dirs()
            s.sort_stats('time', 'calls')
            # writes stats to Stats stream
            s.print_stats()

            # kcachegrind file output
            if convert:
                filename = self.filename_callgrind.format(name=name)
                filename = os.path.join(self.output_dir, filename)
                convert(s, filename)

        # cleanup
        for stream in streams:
            stream.close()
