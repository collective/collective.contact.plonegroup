# -*- coding: utf-8 -*-
def organizations_with_suffixes(groups, suffixes):
    """ Return organization uid with suffixes """
    orgs = []
    for group in groups:
        parts = group.id.split('_')
        if len(parts) == 1:
            continue
        for suffix in suffixes:
            if suffix == parts[1] and parts[0] not in orgs:
                orgs.append(parts[0])
    return orgs
