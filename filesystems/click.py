"""
Click support for `filesystems.Path`.
"""

import click

import filesystems


class Path(click.ParamType):
    """
    A click type for paths.
    """

    name = "path"

    def convert(self, value, param, context):
        """
        Convert the value to a path.
        """
        if not isinstance(value, str):
            return value
        return filesystems.Path.from_string(value)


PATH = Path()
