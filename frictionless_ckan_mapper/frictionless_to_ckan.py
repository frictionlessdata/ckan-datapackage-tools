import json

import slugify

try:
    json_parse_exception = json.decoder.JSONDecodeError
except AttributeError:  # Testing against Python 2
    json_parse_exception = ValueError


class FrictionlessToCKAN:

    resource_mapping = {
        'bytes': 'size',
        'mediatype': 'mimetype',
        'path': 'url'
    }

    package_mapping = {
        'description': 'notes',
        'homepage': 'url',
    }

    # Any key not in this list is passed as is inside "extras".
    # Further processing will happen for possible matchings, e.g.
    # contributor <=> author
    ckan_package_keys = [
        "author",
        "author_email",
        "groups",
        "license_id",
        "maintainer",
        "maintainer_email",
        "name",
        "notes",
        "owner_org",
        "private",
        "relationships_as_object",
        "relationships_as_subject",
        "resources",
        "state",
        "tags",
        "title",
        "type",
        "url",
        "version"
    ]

    def resource(self, fddict):
        '''Convert a Frictionless resource to a CKAN resource.

        # TODO: (the following is inaccurate)

        1. Convert extras: "dict" to "list of dict".
        2. Map keys from Frictionless to CKAN (and reformat if needed).
        3. Apply special formatting (if any) for key fields e.g. slugify.
        4. Map anything not in CKAN inside the "extras" key.
        '''
        pass

    def package(self, fddict):
        '''Convert a Frictionless package to a CKAN package (dataset).

        # TODO: (the following is inaccurate)

        1. Map keys from Frictionless to CKAN (and reformat if needed).
        2. Apply special formatting (if any) for key fields.
        3. Copy extras across inside the "extras" key.
        '''
        outdict = dict(fddict)

        # Map data package keys
        for k, v in self.package_mapping.items():
            if k in fddict:
                outdict[v] = fddict[k]
                del outdict[k]

        if outdict.get('licenses'):
            outdict['license_id'] = outdict['licenses'][0]['type']
            if outdict['licenses'][0].get('title'):
                outdict['license_title'] = outdict['licenses'][0]['title']
            if len(outdict.get('licenses')) > 1:
                if not outdict.get('extras'):
                    outdict['extras'] = []
                outdict['extras'].append({'licenses': outdict['licenses']})
            del outdict['licenses']

        if outdict.get('sources'):
            outdict['author'] = outdict['sources'][0]['title']
            if outdict['sources'][0].get('email'):
                outdict['author_email'] = outdict['sources'][0]['email']
            if outdict['sources'][0].get('path'):
                outdict['url'] = outdict['sources'][0]['path']
            if len(outdict.get('sources')) > 1:
                if not outdict.get('extras'):
                    outdict['extras'] = []
                outdict['extras'].append({'sources': outdict['sources']})
            del outdict['sources']

        if outdict.get('contributors'):
            outdict['maintainer'] = outdict['contributors'][0]['title']
            if outdict['contributors'][0].get('email'):
                outdict['maintainer_email'] = outdict['contributors'][0]['email']

            # Add to "extras" if more than one contributor or if we have fields
            # that can't be mapped directly
            if len(outdict['contributors']) > 1:
                if not outdict.get('extras'):
                    outdict['extras'] = []
                outdict['extras'].append({'contributors': outdict['contributors']})
            else:
                for key in outdict['contributors'][0].keys():
                    if key in ['path', 'organisation', 'role']:
                        if not outdict.get('extras'):
                            outdict['extras'] = []
                            outdict['extras'].append(
                                {'contributors': outdict['contributors']}
                            )
                            break
            del outdict['contributors']

        if outdict.get('keywords'):
            outdict['tags'] = [
                {'name': slugify.slugify(keyword).lower()}
                for keyword in outdict['keywords']
            ]
            del outdict['keywords']

        return outdict
