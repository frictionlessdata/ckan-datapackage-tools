# coding=utf-8

import json

import frictionless_ckan_mapper.ckan_to_frictionless as convert_c2f

import frictionless_ckan_mapper.frictionless_to_ckan as convert_f2c

import six


class TestResourceConversion:
    '''Notes:

    * extras do not any special testing since CKAN already just has them as key
      values.
    * we do want to test unjsonifying values since that will cover e.g. a Table
      Schema set in schema field
    '''

    def test_fixtures(self):
        # Test simple conversion
        inpath = 'tests/fixtures/ckan_resource.json'
        exppath = 'tests/fixtures/frictionless_resource.json'
        indict = json.load(open(inpath))
        exp = json.load(open(exppath))
        out = convert_c2f.resource(indict)
        assert out == exp

    def test_values_are_unjsonified(self):
        '''Test values which are jsonified dict or arrays are unjsonified'''
        schema = {
            "fields": [
                {"name": "abc", "type": "string"}
            ]
        }
        indict = {
            "schema": json.dumps(schema),
            "otherval": json.dumps(schema),
            "x": "{'abc': 1"
        }
        exp = {
            "schema": schema,
            "otherval": schema,
            # fake json object - not really ... but looks like it ...
            "x": "{'abc': 1"
        }
        out = convert_c2f.resource(indict)
        assert out == exp

        indict = {
            "x": "hello world",
            "y": "1.3"
        }
        exp = {
            "x": "hello world",
            "y": "1.3"
        }
        out = convert_c2f.resource(indict)
        assert out == exp

    def test_keys_are_removed_that_should_be(self):
        indict = {
            "package_id": "xxx",
            "position": 2,
            "datastore_active": True,
            "state": "active"
        }
        exp = {}
        out = convert_c2f.resource(indict)
        assert out == exp

    def test_resource_mapping(self):
        indict = {
            "url": "http://www.somewhere.com/data.csv",
            "size": 110,
            "mimetype": "text/csv"
        }
        exp = {
            "path": "http://www.somewhere.com/data.csv",
            "bytes": 110,
            "mediatype": "text/csv"
        }
        out = convert_c2f.resource(indict)
        assert out == exp

    def test_resource_path_is_set_even_for_uploaded_resources(self):
        indict = {
            "url": "http://www.somewhere.com/data.csv",
            "url_type": "upload"
        }
        exp = {
            'path': 'http://www.somewhere.com/data.csv',
            'url_type': "upload"
        }
        out = convert_c2f.resource(indict)
        assert out == exp

    def test_resource_keys_pass_through(self):
        indict = {
            'description': 'GDPs list',
            'format': 'CSV',
            'hash': 'e785c0883d7a104330e69aee73d4f235',
            'schema': {
                'fields': [
                    {'name': 'id', 'type': 'integer'},
                    {'name': 'title', 'type': 'string'},
                ]
            },
            # random
            'adfajka': 'aaaa',
            '1dafak': 'abbbb'
        }
        exp = indict
        out = convert_c2f.resource(indict)
        assert out == exp

    def test_nulls_are_stripped(self):
        indict = {
            'abc': 'xxx',
            'size': None,
            'xyz': None
        }
        exp = {
            'abc': 'xxx'
        }
        out = convert_c2f.resource(indict)
        assert out == exp


class TestPackageConversion:
    def test_dataset_extras(self):
        indict = {
            'extras': [
                {'key': 'title_cn', 'value': u'國內生產總值'},
                {'key': 'years', 'value': '[2015, 2016]'},
                {'key': 'last_year', 'value': 2016},
                {'key': 'location', 'value': '{"country": "China"}'}
            ]
        }
        exp = {
            'title_cn': u'國內生產總值',
            'years': [2015, 2016],
            'last_year': 2016,
            'location': {'country': 'China'}
        }
        out = convert_c2f.dataset(indict)
        assert out == exp

    def test_unjsonify_all_extra_values(self):
        indict = {
            'extras': [
                {
                    'key': 'location',
                    'value': '{"country": {"China": {"population": '
                             '"1233214331", "capital": "Beijing"}}}'
                },
                {
                    'key': 'numbers',
                    'value': '[[[1, 2, 3], [2, 4, 5]], [[7, 6, 0]]]'
                }
            ]
        }
        out = convert_c2f.dataset(indict)
        exp = {
            "location": {
                "country":
                {"China":
                 {"population": "1233214331",
                  "capital": "Beijing"}}
            },
            "numbers": [[[1, 2, 3], [2, 4, 5]], [[7, 6, 0]]]
        }
        assert out == exp

    def test_dataset_license(self):
        # No license_title nor license_url
        indict = {
            'license_id': 'odc-odbl'
        }
        exp = {
            'licenses': [{
                'name': 'odc-odbl',
            }]
        }
        out = convert_c2f.dataset(indict)
        assert out == exp

        # Remap everything in licenses
        indict = {
            'license_id': 'cc-by',
            'license_title': 'Creative Commons Attribution',
            'license_url': 'http://www.opendefinition.org/licenses/cc-by'
        }
        exp = {
            'licenses': [{
                'name': 'cc-by',
                'title': 'Creative Commons Attribution',
                'path': 'http://www.opendefinition.org/licenses/cc-by'
            }]
        }
        out = convert_c2f.dataset(indict)
        assert out == exp

    def test_dataset_license_with_licenses_in_extras(self):
        indict = {
            'license_id': 'odc-odbl',
            'license_title': 'Open Data Commons Open Database License',
            'license_url': 'https://opendatacommons.org/licenses/odbl/1-0/index.html',
            'extras': [
                {
                    'key': 'licenses',
                    'value': json.dumps(
                        [
                            {
                                'name': 'cc-by',
                                'title': 'Creative Commons Attribution',
                                'path': 'http://www.opendefinition.org/licenses/cc-by'
                            },
                            {
                                'name': 'odc-by',
                                'title': 'Open Data Commons Attribution License',
                                'path': 'https://opendatacommons.org/licenses/by/1-0/index.html'
                            }
                        ]
                    )
                }
            ]
        }
        exp = {
            'licenses': [
                {
                    'name': 'odc-odbl',
                    'title': 'Open Data Commons Open Database License',
                    'path': 'https://opendatacommons.org/licenses/odbl/1-0/index.html'
                },
                {
                    'name': 'odc-by',
                    'title': 'Open Data Commons Attribution License',
                    'path': 'https://opendatacommons.org/licenses/by/1-0/index.html'
                }
            ]
        }
        out = convert_c2f.dataset(indict)
        assert out == exp

    def test_keys_are_passed_through(self):
        indict = {
            'name': 'gdp',
            'title': 'Countries GDP',
            'version': '1.0',
            # random
            'xxx': 'aldka'
        }
        out = convert_c2f.dataset(indict)
        exp = {
            'name': 'gdp',
            'title': 'Countries GDP',
            'version': '1.0',
            'xxx': 'aldka'
        }
        assert out == exp

    def test_key_mappings(self):
        # notes
        indict = {
            'notes': 'Country, regional and world GDP',
            'url': 'https://datopian.com'
        }
        exp = {
            'description': 'Country, regional and world GDP',
            'homepage': 'https://datopian.com'
        }
        out = convert_c2f.dataset(indict)
        assert out == exp

    def test_dataset_author_and_maintainer(self):
        indict = {
            'author': 'World Bank and OECD',
            'author_email': 'someone@worldbank.org'
        }
        exp = {
            'contributors': [
                {
                    'title': 'World Bank and OECD',
                    'email': 'someone@worldbank.org',
                    'role': 'author'
                }
            ]
        }
        out = convert_c2f.dataset(indict)
        assert out == exp

        indict = {
            'author': 'World Bank and OECD',
            'author_email': 'someone@worldbank.org',
            'maintainer': 'Datopian',
            'maintainer_email': 'helloxxx@datopian.com'
        }
        exp = {
            'contributors': [
                {
                    'title': 'World Bank and OECD',
                    'email': 'someone@worldbank.org',
                    'role': 'author'
                },
                {
                    'title': 'Datopian',
                    'email': 'helloxxx@datopian.com',
                    'role': 'maintainer'
                },

            ]
        }
        out = convert_c2f.dataset(indict)
        assert out == exp

        # if we already have contributors use that ...
        indict = {
            'contributors': [{
                'title': 'Datopians'
            }],
            'author': 'World Bank and OECD',
        }
        exp = {
            'contributors': [{
                'title': 'Datopians'
            }]
        }
        out = convert_c2f.dataset(indict)
        assert out == exp

    def test_dataset_tags(self):
        indict = {
            'tags': [
                {
                    'display_name': 'economy',
                    'id': '9d602a79-7742-44a7-9029-50b9eca38c90',
                    'name': 'economy',
                    'state': 'active'
                },
                {
                    'display_name': 'worldbank',
                    'id': '3ccc2e3b-f875-49ef-a39d-6601d6c0ef76',
                    'name': 'worldbank',
                    'state': 'active'
                }
            ]
        }
        exp = {
            'keywords': ['economy', 'worldbank']
        }
        out = convert_c2f.dataset(indict)
        assert out == exp

    def test_resources_are_converted(self):
        # Package has multiple resources
        resource_1 = {
            'id': '1234',
            'name': 'data.csv',
            'url': 'http://someplace.com/data.csv'
        }
        resource_2 = {
            'id': '12345',
            'name': 'data2.csv',
            'url': 'http://someotherplace.com/data2.csv'
        }
        indict_2_resources = {
            'name': 'gdp',
            'title': 'Countries GDP',
            'resources': [resource_1, resource_2]
        }
        indict_1_resource = {
            'name': 'gdp',
            'title': 'Countries GDP',
            'resources': [resource_1]
        }
        out = convert_c2f.dataset(indict_2_resources)
        assert len(out['resources']) == 2

        # Package has a single resource
        out = convert_c2f.dataset(indict_1_resource)
        assert len(out['resources']) == 1

    def test_all_keys_are_passed_through(self):
        indict = {
            'description': 'GDPs list',
            'schema': {
                'fields': [
                    {'name': 'id', 'type': 'integer'},
                    {'name': 'title', 'type': 'string'},
                ]
            },
            # random
            'adfajka': 'aaaa',
            '1dafak': 'abbbb'
        }
        exp = indict
        out = convert_c2f.resource(indict)
        assert out == exp

    def test_keys_are_removed_that_should_be(self):
        indict = {
            'state': 'active'
        }
        exp = {
        }
        out = convert_c2f.dataset(indict)
        assert out == exp

    def test_null_values_are_stripped(self):
        indict = {
            'id': '12312',
            'title': 'title here',
            'format': None
        }
        exp = {
            'id': '12312',
            'title': 'title here'
        }
        out = convert_c2f.dataset(indict)
        assert out == exp

    def test_round_trip_ckan(self):
        # `ckan1` != `ckan2` but `ckan2` == `ckan3`
        inpath = 'tests/fixtures/full_ckan_package.json'
        ckan1 = json.load(open(inpath))
        fd1 = convert_c2f.dataset(ckan1)
        ckan2 = convert_f2c.package(fd1)
        fd2 = convert_c2f.dataset(ckan2)
        ckan3 = convert_f2c.package(fd2)
        
        # FIXME: this currently doesn't work for Python 2 due to the way
        # Unicode is handled and because the dictionary keys do not keep
        # the same order.
        # Solution 1: Skip for Python 2 (it's clearly the same dictionary
        # if the build passes on Python 3)
        # Solution 2: Hard code the dicts as in `test_extras_is_converted`
        # in test_frictionless_to_ckan.py instead of loading JSON and
        # sort the keys.
        if not six.PY2:
            assert ckan2 == ckan3

    def test_differences_ckan_round_trip(self):
        # When converting ckan1 to fd1 then fd1 to ckan2,
        # ckan1 is bound to differ from ckan2.
        # Those fixtures illustrate the expected differences.
        inpath = 'tests/fixtures/full_ckan_package.json'
        ckan1 = json.load(open(inpath))
        fd1 = convert_c2f.dataset(ckan1)
        ckan2 = convert_f2c.package(fd1)
        inpath_round_trip = ('tests/fixtures/'
                             'full_ckan_package_first_round_trip.json')
        exp = json.load(open(inpath_round_trip))

        # FIXME: this currently doesn't work for Python 2 due to the way
        # Unicode is handled and because the dictionary keys do not keep
        # the same order.
        # Solution 1: Skip for Python 2 (it's clearly the same dictionary
        # if the build passes on Python 3)
        # Solution 2: Hard code the dicts as in `test_extras_is_converted`
        # in test_frictionless_to_ckan.py instead of loading JSON and
        # sort the keys.
        if not six.PY2:
            assert ckan2 == exp

        # Notable differences in `exp` from ckan1 are:
        # - Keys not defined in a standard CKAN package such as
        #  `creator_user_id` will go to `extras`.
        # - In our `full_ckan_package.json` fixture, 'extras' is empty but
        #   Frictionless fills it and it will exist in the CKAN package after
        #   the first round trip.
        # - Keys defined in CKAN but ignored in Frictionless, such as `id`
        #   (because a Frictionless package doesn't have an id property) will
        #   also go to 'extras'.
