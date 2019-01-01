import sys
_PY3 = sys.version_info[0] >= 3

from pkg_resources import get_distribution, DistributionNotFound
try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:  # pragma: no cover
    pass

from filesystems._path import Path

