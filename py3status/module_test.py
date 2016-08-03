import inspect
from time import sleep
from py3status.py3 import Py3


def module_test(module_class, config=None):
    i3s_config = {
        'color_bad': '#FF0000',
        'color_degraded': '#FFFF00',
        'color_good': '#00FF00'
    }
    module = module_class()
    setattr(module, 'py3', Py3(i3s_config=i3s_config))
    if config:
        for key, value in config.items():
            setattr(module, key, value)
    methods = []
    for method_name in sorted(dir(module)):
        if method_name.startswith('_'):
            continue
        if method_name in ['on_click', 'kill', 'py3']:
            continue
        if not hasattr(getattr(module_class, method_name, ''), '__call__'):
            continue

        method = getattr(module, method_name, None)
        args, vargs, kw, defaults = inspect.getargspec(method)
        if len(args) == 1:
            methods.append((method_name, []))
        else:
            methods.append((method_name, [[], i3s_config]))
    while True:
        try:
            for method, method_args in methods:
                print(getattr(module, method)(*method_args))
            sleep(1)
        except KeyboardInterrupt:
            break
            if hasattr(module, 'kill'):
                method = getattr(module, 'kill', None)
                args, vargs, kw, defaults = inspect.getargspec(method)
                if len(args) == 1:
                    module.kill()
                else:
                    module.kill([], i3s_config)
            break
