import json

import cibuildwheel.linux
import cibuildwheel.macos
from cibuildwheel.architecture import Architecture
from cibuildwheel.util import BuildSelector


def _main():
    build_selector = BuildSelector(
        build_config="*",
        skip_config="",
        requires_python=None,
        prerelease_pythons=None
    )

    linux_python_configurations = cibuildwheel.linux.get_python_configurations(
        build_selector,
        {Architecture.x86_64, Architecture.aarch64},
    )

    macos_python_configurations = cibuildwheel.macos.get_python_configurations(
        build_selector,
        {Architecture.x86_64}
    )

    matrix = {
        "include": [
            {
                "os": "ubuntu-20.04",
                "CIBW_ARCHS": _configuration_to_architecture(configuration).value,
                "CIBW_BUILD": configuration.identifier,
            }
            for configuration in linux_python_configurations
        ] + [
            {
                "os": "macos-10.15",
                "CIBW_ARCHS": _configuration_to_architecture(configuration).value,
                "CIBW_BUILD": configuration.identifier,
            }
            for configuration in macos_python_configurations
        ]
    }

    print("::set-output name=matrix::" + json.dumps(matrix))


def _configuration_to_architecture(configuration):
    for architecture in Architecture:
        if configuration.identifier.endswith(f"_{architecture.value}"):
            return architecture

    raise ValueError("could not find architecture for configuration")


if __name__ == "__main__":
    _main()
