r"""
Display properties of running docker containers.

Configuration parameters:
    containers: filter the list by container or image name (default [])
    delimiter: separator between containers (default ' ')
    format: format to display each container (default '{name} {image}')

Format placeholders:
    {name} instance name (--name= on run, or randomly generated)
    {short_id} shortened unique container id
    {id} full container id
    {status} running state of container
    {image} name of the image running in the container
    {gateway} the gateway IP to interact with the container

Requires:
    docker: python client for the docker container engine

Examples:
```
docker {
    containers = ["mysql:*"]
    delimiter = "|"
    format = "{name}({image})- {gateway}"
}
```

@author la kevna (Aaron Moore)

SAMPLE OUTPUT
{'full_text': u'vigorous_ride mysql:latest'}
"""

import docker
from fnmatch import fnmatch


class Py3status:
    """
    """

    # available configuration parameters
    containers = []
    delimiter = " "
    format = "{name} {image}"

    def post_config_hook(self):
        self.client = docker.from_env()

    def _match_containers(self):
        containers = self.client.containers.list()
        if self.containers:
            for container in containers:
                if any(
                    fnmatch(container.attrs["Config"]["Image"], glob)
                    for glob in self.containers
                ) or any(fnmatch(container.name, glob) for glob in self.containers):
                    yield container
        else:
            yield from containers

    def _print(self, container):
        return self.format.format(
            name=container.name,
            short_id=container.short_id,
            id=container.id,
            status=container.status,
            image=container.attrs["Config"]["Image"],
            gateway=container.attrs["NetworkSettings"]["Gateway"]
        )

    def docker(self):
        """
        docker response
        """
        text = []
        for container in self._match_containers():
            text.append(self._print(container))
        return {"full_text": self.delimiter.join(text)}


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
