import json

try:
    json_parse_exception = json.decoder.JSONDecodeError
except AttributeError:  # Testing against Python 2
    json_parse_exception = ValueError


resource_mapping = {
    'size': 'bytes',
    'mimetype': 'mediatype',
    'url': 'path'
}

resource_keys_to_remove = [
    'package_id',
    'position',
    'datastore_active',
    'state'
]


def resource(ckandict):
    '''Convert a CKAN resource to Frictionless Resource.

    1. Remove unneeded keys
    2. Expand extras.
        * Extras are already expanded to key / values by CKAN (unlike on
            package)
        * ~~Apply heuristic to unjsonify (if starts with [ or { unjsonify~~
        * JSON loads everything that starts with [ or {
    3. Map keys from CKAN to Frictionless (and reformat if needed)
    4. Remove keys with null values (CKAN has a lot of null valued keys)
    5. Apply special formatting (if any) for key fields e.g. slugiify
    '''
    # TODO: delete keys last as may be needed for something in processing
    resource = dict(ckandict)
    for key in resource_keys_to_remove:
        if key in resource:
            del resource[key]

    # unjsonify values
    # * check if string
    # * if starts with [ or { => json.loads it ...
    # HACK: bit of a hacky way to check if value is a jsonified array or
    # dict
    # * else do nothing
    for key, value in resource.items():
        if isinstance(value, str):
            value = value.strip()
            if value.startswith('{') or value.startswith('['):
                try:
                    value = json.loads(value)
                    resource[key] = value
                except (json_parse_exception, TypeError):
                    pass

    # Remap differences from CKAN to Frictionless resource
    for key, value in resource_mapping.items():
        if key in resource:
            resource[value] = resource[key]
            del resource[key]

    for key in list(resource.keys()):
        if resource[key] is None:
            del resource[key]

    return resource


dataset_keys_to_remove = [
    'state'
]
dataset_mapping = {
    'notes': 'description',
    'url': 'homepage'
}


def dataset(ckandict):
    '''Convert a CKAN Package (Dataset) to Frictionless Package.

    1. Expand extras.
        * JSON loads everything and on error have a string
    2. Map keys from CKAN to Frictionless (and reformat if needed)
    3. Remove keys with null values (CKAN has a lot of null valued keys)
    4. Remove unneeded keys
    5. Apply special formatting for key fields
    '''
    outdict = dict(ckandict)
    # Convert the structure of extras
    # structure of extra item is {key: xxx, value: xxx}
    if 'extras' in ckandict:
        for extra in ckandict['extras']:
            key = extra['key']
            value = extra['value']
            try:
                value = json.loads(value)
            except (json_parse_exception, TypeError):
                pass
            outdict[key] = value
        del outdict['extras']

    # Map dataset keys
    for key, value in dataset_mapping.items():
        if key in ckandict:
            outdict[value] = ckandict[key]
            del outdict[key]

    # tags
    if 'tags' in ckandict:
        outdict['keywords'] = [tag['name'] for tag in ckandict['tags']]
        del outdict['tags']

    # author, maintainer => contributors
    # what to do if contributors already there? Options:
    # 1. Just use that and ignore author/maintainer
    # 2. replace with author/maintainer
    # 3. merge i.e. use contributors and merge in (this is sort of complex)
    # e.g. how to i avoid duplicating the same person
    # ANS: for now, is 1 ...
    if (not ('contributors' in outdict and outdict['contributors']) and
            ('author' in outdict or 'maintainer' in outdict)):
        outdict['contributors'] = []
        if 'author' in outdict and outdict['author']:
            contrib = {
                'title': outdict['author'],
                'role': 'author'
            }
            if 'author_email' in outdict:
                contrib['email'] = outdict['author_email']
            outdict['contributors'].append(contrib)
        if 'maintainer' in outdict and outdict['maintainer']:
            contrib = {
                'title': outdict['maintainer'],
                'role': 'maintainer'
            }
            if 'maintainer_email' in outdict:
                contrib['email'] = outdict['maintainer_email']
            outdict['contributors'].append(contrib)

    for key in ['author', 'author_email', 'maintainer', 'maintainer_email']:
        outdict.pop(key, None)

    # Reformat resources inside dataset
    if 'resources' in outdict:
        outdict['resources'] = [resource(res) for res in
                                outdict['resources']]

    # package_show can have license_id and license_title
    # TODO: do we always license_id i.e. can we have license_title w/o
    # license_id?
    # There's no mention in the docs of license_title nor license_url, plus
    # license_id is listed as optional in both CKAN 2.8 and 2.9.

    # Looping like this because all those keys are optional.
    for key in ['license_id', 'license_title', 'license_url']:
        if key in outdict:
            outdict['licenses'] = [{}]
            break  # check to create list of dicts only once
    if 'license_id' in outdict:
        outdict['licenses'][0]['name'] = outdict['license_id']
    if 'license_title' in outdict:
        outdict['licenses'][0]['title'] = outdict['license_title']
    if 'license_url' in outdict:
        outdict['licenses'][0]['path'] = outdict['license_url']
    outdict.pop('license_id', None)
    outdict.pop('license_title', None)
    outdict.pop('license_url', None)

    # Check `ckandict` instead of `outdict` because outdict['extras']
    # was deleted earlier
    licenses_there = False  # First assume we won't find licenses
    if ckandict.get('extras'):
        for item in ckandict['extras']:  # this is a list
            if not licenses_there:
                for value in item.values():  # dicts inside list
                    # dict containing {'key': 'licenses', 'value': '...'}
                    if value == 'licenses':
                        licenses_there = True
                        licenses_dict = dict(item).get('value')  # dict as str
                        licenses_dict = json.loads(licenses_dict)  # get dict
                        licenses_list = licenses_dict.get('licenses')  # list
                        break
        if licenses_there:
            for license in licenses_list:  # list of dicts
                license_out = {}  # won't be empty, create it now to be filled
                if 'name' in license:
                    license_out['name'] = license['name']
                if 'title' in license:
                    license_out['title'] = license['title']
                if 'path' in license:
                    license_out['path'] = license['path']
                if license_out not in outdict['licenses']:  # avoid duplicates
                    outdict['licenses'].append(license_out)

    for key in dataset_keys_to_remove:
        outdict.pop(key, None)

    for key in list(outdict.keys()):
        if outdict[key] is None:
            del outdict[key]

    return outdict
