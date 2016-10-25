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
    setattr(module, 'py3', Py3(i3s_config=i3s_config, py3status=module))
    if config:
        for key, value in config.items():
            setattr(module, key, value)
    methods = []

    for attribute_name in sorted(dir(module)):
        # find methods that we should test.
        attribute = getattr(module, attribute_name)

        if 'method' not in repr(attribute):
            continue
        if attribute_name.startswith('_'):
            continue
        if attribute_name in ['on_click', 'kill', 'py3', 'post_config_hook']:
            continue

        # set calling parameter for method to allow legacy calling signature
        args, vargs, kw, defaults = inspect.getargspec(attribute)
        if len(args) == 1:
            methods.append((attribute_name, []))
        else:
            methods.append((attribute_name, [[], i3s_config]))

    # If we are a container then self.items must be set as a list
    try:
        if module.Meta.container:
            module.items = []
    except AttributeError:
        pass

    # run any post_config_hook
    if hasattr(module, 'post_config_hook'):
        module.post_config_hook()

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
