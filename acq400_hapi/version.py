"""Determine the current version of the package"""

import git
import os.path

MODULE_DIR = os.path.dirname(__file__)


def get_version():
    """Return a valid version string from the latest Git tag of the current checkout.
    Drop the leading `v`, separate public x.y.z version from git hash with a `+`, replace
    remaining `-` with `.`. Should work on all platforms"""
    repo = git.Repo(MODULE_DIR, search_parent_directories=True)
    v = repo.git.describe('--tags')
    # e.g. 'v2.14.1-7-g914b5d0': 7 commits after last tag, v2.14.1, with hash 914b5d0
    v = v.lstrip('v') # e.g. '2.14.1-7-g914b5d0'
    v, _, gh = v.partition('-') # e.g. '2.14.1', '-', '7-g914b5d0'
    if gh:
        gh = gh.replace('-', '.') # e.g. '7.g914b5d0'
        return v + '+' + gh # e.g. '2.14.1+7.g914b5d0'
    else: # gh == ''
        return v # e.g. '2.14.1'
