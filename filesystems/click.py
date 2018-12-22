"""
Click support for `filesystems.Path`.
"""

from __future__ import absolute_import
import click

import filesystems


class Path(click.ParamType):

    name = "path"

    def convert(self, value, param, context):
        if not isinstance(value, str):
            return value
        return filesystems.Path.from_string(value)


PATH = Path()
