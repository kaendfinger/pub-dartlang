# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import json

from google.appengine.api import users

from testcase import TestCase
from models.package import Package
from models.semantic_version import SemanticVersion

class PackagesTest(TestCase):
    def test_index_lists_packages_in_update_order(self):
        self.be_admin_user()

        packages = ['armadillo', 'zebra', 'mongoose', 'snail']

        for package in packages:
            self.create_package(package, '1.0.0')

        # Make update time different than create time
        self.set_latest_version('mongoose', '1.0.1')

        self.expect_lists_packages(['mongoose', 'snail', 'zebra', 'armadillo'])

    def test_index_lists_one_page_of_packages(self):
        self.be_admin_user()

        packages = [
            'armadillo', 'bat', 'crocodile', 'dragon', 'elephant', 'frog',
            'gorilla', 'headcrab', 'ibex', 'jaguar', 'kangaroo', 'llama'
        ]

        for package in packages:
            self.create_package(package, '1.0.0')

        # Only the ten most recent packages should be listed
        self.expect_lists_packages([
                'llama', 'kangaroo', 'jaguar', 'ibex', 'headcrab', 'gorilla',
                'frog', 'elephant', 'dragon', 'crocodile'])

    def test_page_two_lists_second_page_of_packages(self):
        self.be_admin_user()

        packages = [
            'armadillo', 'bat', 'crocodile', 'dragon', 'elephant', 'frog',
            'gorilla', 'headcrab', 'ibex', 'jaguar', 'kangaroo', 'llama'
        ]

        for package in packages:
            self.create_package(package, '1.0.0')

        # Only the ten most recent packages should be listed
        self.expect_lists_packages(['bat', 'armadillo'], page=2)

    def test_get_non_existent_package(self):
        self.testapp.get('/packages/package/test-package', status=404)

    def test_get_unowned_package(self):
        self.be_admin_user()
        Package.new(name='test-package').put()

        self.be_normal_user()
        response = self.testapp.get('/packages/test-package')
        self.assert_no_link(response, '/packages/test-package/versions/new')

    def test_get_owned_package(self):
        self.be_admin_user()
        Package.new(name='test-package').put()

        response = self.testapp.get('/packages/test-package')
        self.assert_link(response, '/packages/test-package/versions/new')

    def test_get_package_json_without_versions(self):
        admin = self.admin_user()
        Package.new(name='test-package', owner=admin).put()

        response = self.testapp.get('/packages/test-package.json')
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        self.assertEqual(json.loads(response.body), {
            "name": "test-package",
            "owner": admin.email(),
            "versions": []
        })

    def test_get_package_json_with_versions(self):
        admin = self.admin_user()
        package = Package.new(name='test-package', owner=admin)
        package.put()

        self.package_version(package, '1.1.0').put()
        self.package_version(package, '1.1.1').put()
        self.package_version(package, '1.2.0').put()

        response = self.testapp.get('/packages/test-package.json')
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        self.assertEqual(json.loads(response.body), {
            "name": "test-package",
            "owner": admin.email(),
            "versions": ['1.1.0', '1.1.1', '1.2.0']
        })

    def expect_lists_packages(self, expected_order, page=1):
        """Assert that the package index lists packages in a particular order.

        Arguments:
          expected_order: A list of package names.
        """
        url = '/packages'
        if page != 1: url += '?page=%d' % page
        self.assert_list_in_html(url, "tbody tr", expected_order)
