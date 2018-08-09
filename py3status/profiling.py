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
            thread_id = getattr(self, "ident", "core")
            profiler.dump_stats("py3status-%s.profile" % thread_id)

    return wrapper_run
