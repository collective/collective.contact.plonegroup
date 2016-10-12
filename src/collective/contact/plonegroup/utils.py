# -*- coding: utf-8 -*-
def organizations_with_suffixes(groups, suffixes):
    """
        Return organization uids for given plone groups and without suffixes
    """
    orgs = []
    for group in groups:
        parts = group.id.split('_')
        if len(parts) == 1:
            continue
        group_suffix = '_'.join(parts[1:])
        if group_suffix in suffixes and parts[0] not in orgs:
            orgs.append(parts[0])
    return orgs
