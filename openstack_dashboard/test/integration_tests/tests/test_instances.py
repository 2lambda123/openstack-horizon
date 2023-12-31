#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from openstack_dashboard.test.integration_tests import helpers
from openstack_dashboard.test.integration_tests.regions import messages


class TestInstances(helpers.TestCase):
    INSTANCE_NAME = helpers.gen_random_resource_name('instance',
                                                     timestamp=False)

    @property
    def instances_page(self):
        return self.home_pg.go_to_project_compute_instancespage()

    def test_create_delete_instance(self):
        """tests the instance creation and deletion functionality:

        * creates a new instance in Project > Compute > Instances page
        * verifies the instance appears in the instances table as active
        * deletes the newly created instance via proper page (depends on user)
        * verifies the instance does not appear in the table after deletion
        """
        instances_page = self.home_pg.go_to_project_compute_instancespage()

        instances_page.create_instance(self.INSTANCE_NAME)
        self.assertEqual(
            instances_page.find_messages_and_dismiss(), {messages.INFO})
        self.assertTrue(instances_page.is_instance_active(self.INSTANCE_NAME))

        instances_page = self.instances_page
        instances_page.delete_instance(self.INSTANCE_NAME)
        self.assertEqual(
            instances_page.find_messages_and_dismiss(), {messages.INFO})
        self.assertTrue(instances_page.is_instance_deleted(self.INSTANCE_NAME))


class TestInstancesPagination(helpers.TestCase):
    INSTANCE_NAME = helpers.gen_random_resource_name('instance',
                                                     timestamp=False)
    ITEMS_PER_PAGE = 1
    INSTANCE_COUNT = 2

    @property
    def instances_page(self):
        return self.home_pg.go_to_project_compute_instancespage()

    def setUp(self):
        super().setUp()
        self.instance_list = ["{0}-{1}".format(self.INSTANCE_NAME, item)
                              for item in range(1, self.INSTANCE_COUNT + 1)]

        instances_page = self.instances_page

        # delete any old instances
        garbage = instances_page.instances_table.get_column_data(
            name_column='Instance Name')
        if garbage:
            instances_page.delete_instances(garbage)
            self.assertEqual(
                instances_page.find_messages_and_dismiss(), {messages.INFO})
            self.assertTrue(
                instances_page.are_instances_deleted(garbage))

        instances_page.create_instance(self.INSTANCE_NAME,
                                       instance_count=self.INSTANCE_COUNT)
        self.assertEqual(
            instances_page.find_messages_and_dismiss(), {messages.INFO})
        self.assertTrue(
            instances_page.is_instance_active(self.instance_list[1]))

        settings_page = self.home_pg.go_to_settings_usersettingspage()
        settings_page.change_pagesize(self.ITEMS_PER_PAGE)
        self.assertEqual(
            settings_page.find_messages_and_dismiss(), {messages.SUCCESS})

        def cleanup():
            settings_page = self.home_pg.go_to_settings_usersettingspage()
            settings_page.change_pagesize()
            self.assertEqual(
                settings_page.find_messages_and_dismiss(), {messages.SUCCESS})

            instances_page = self.instances_page
            instances_page.delete_instances(self.instance_list)
            self.assertEqual(
                instances_page.find_messages_and_dismiss(), {messages.INFO})
            self.assertTrue(
                instances_page.are_instances_deleted(self.instance_list))

        self.addCleanup(cleanup)

    def test_instances_pagination(self):
        """This test checks instance pagination

        Steps:
        1) Login to Horizon Dashboard as regular user
        2) Navigate to user settings page
        3) Change 'Items Per Page' value to 1
        4) Go to Project > Compute > Instances page
        5) Create 2 instances
        6) Go to appropriate page (depends on user)
        7) Check that only 'Next' link is available, only one instance is
           available (and it has correct name) on the first page
        8) Click 'Next' and check that on the second page only one instance is
           available (and it has correct name), there is no 'Next' link on page
        9) Go to user settings page and restore 'Items Per Page'
        10) Delete created instances via proper page (depends on user)
        """
        first_page_definition = {'Next': True, 'Prev': False,
                                 'Count': self.ITEMS_PER_PAGE,
                                 'Names': [self.instance_list[1]]}
        second_page_definition = {'Next': False, 'Prev': True,
                                  'Count': self.ITEMS_PER_PAGE,
                                  'Names': [self.instance_list[0]]}

        instances_page = self.instances_page

        instances_page = self.instances_page
        instances_page.instances_table.assert_definition(
            first_page_definition, sorting=True, name_column="Instance Name")

        instances_page.instances_table.turn_next_page()
        instances_page.instances_table.assert_definition(
            second_page_definition, sorting=True, name_column="Instance Name")

        instances_page = self.instances_page
        instances_page.instances_table.assert_definition(
            first_page_definition, sorting=True, name_column="Instance Name")

    def test_instances_pagination_and_filtration(self):
        """This test checks instance pagination and filtration

        Steps:
        1) Login to Horizon Dashboard as regular user
        2) Go to to user settings page
        3) Change 'Items Per Page' value to 1
        4) Go to Project > Compute > Instances page
        5) Create 2 instances
        6) Go to appropriate page (depends on user)
        7) Check filter by Name of the first and the second instance in order
           to have one instance in the list (and it should have correct name)
           and no 'Next' link is available
        8) Check filter by common part of Name of in order to have one instance
           in the list (and it should have correct name) and 'Next' link is
           available on the first page and is not available on the second page
        9) Go to user settings page and restore 'Items Per Page'
        10) Delete created instances via proper page (depends on user)

        """
        first_page_definition = {'Next': True, 'Prev': False,
                                 'Count': self.ITEMS_PER_PAGE,
                                 'Names': [self.instance_list[1]]}
        second_page_definition = {'Next': False, 'Prev': False,
                                  'Count': self.ITEMS_PER_PAGE,
                                  'Names': [self.instance_list[0]]}
        filter_first_page_definition = {'Next': False, 'Prev': False,
                                        'Count': self.ITEMS_PER_PAGE,
                                        'Names': [self.instance_list[1]]}

        instances_page = self.instances_page
        instances_page.instances_table.set_filter_value('name')
        instances_page.instances_table.filter(self.instance_list[1])
        instances_page.instances_table.assert_definition(
            filter_first_page_definition, sorting=True,
            name_column="Instance Name")

        instances_page.instances_table.filter(self.instance_list[0])
        instances_page.instances_table.assert_definition(
            second_page_definition, sorting=True,
            name_column="Instance Name")

        instances_page.instances_table.filter(self.INSTANCE_NAME)
        instances_page.instances_table.assert_definition(
            first_page_definition, sorting=True,
            name_column="Instance Name")
        instances_page.instances_table.filter('')


class TestInstancesFilter(helpers.TestCase):
    INSTANCE_NAME = helpers.gen_random_resource_name('instance',
                                                     timestamp=False)
    INSTANCE_COUNT = 2

    @property
    def instances_page(self):
        return self.home_pg.go_to_project_compute_instancespage()

    def setUp(self):
        super().setUp()
        self.instance_list = ["{0}-{1}".format(self.INSTANCE_NAME, item)
                              for item in range(1, self.INSTANCE_COUNT + 1)]
        instances_page = self.instances_page

        # delete any old instances
        garbage = instances_page.instances_table.get_column_data(
            name_column='Instance Name')
        if garbage:
            instances_page.delete_instances(garbage)
            self.assertEqual(
                instances_page.find_messages_and_dismiss(), {messages.INFO})
            self.assertTrue(
                instances_page.are_instances_deleted(garbage))

        instances_page.create_instance(self.INSTANCE_NAME,
                                       instance_count=self.INSTANCE_COUNT)
        self.assertEqual(
            instances_page.find_messages_and_dismiss(), {messages.INFO})
        self.assertTrue(
            instances_page.is_instance_active(self.instance_list[1]))

        def cleanup():
            instances_page = self.instances_page
            instances_page.delete_instances(self.instance_list)
            self.assertEqual(
                instances_page.find_messages_and_dismiss(), {messages.INFO})
            self.assertTrue(
                instances_page.are_instances_deleted(self.instance_list))

        self.addCleanup(cleanup)

    def test_filter_instances(self):
        """This test checks filtering of instances by Instance Name

        Steps:
        1) Login to Horizon dashboard as regular user
        2) Go to Project > Compute > Instances
        3) Create 2 instances
        4) Go to appropriate page (depends on user)
        5) Use filter by Instance Name
        6) Check that filtered table has one instance only (which name is equal
           to filter value) and no other instances in the table
        7) Check that filtered table has both instances (search by common part
           of instance names)
        8) Set nonexistent instance name. Check that 0 rows are displayed
        9) Clear filter and delete instances via proper page (depends on user)
        """

        instances_page = self.instances_page
        instances_page.instances_table.set_filter_value('name')

        instances_page.instances_table.filter(self.instance_list[0])
        self.assertTrue(
            instances_page.is_instance_present(self.instance_list[0]))
        for instance in self.instance_list[1:]:
            self.assertFalse(instances_page.is_instance_present(instance))

        instances_page.instances_table.filter(self.INSTANCE_NAME)
        for instance in self.instance_list:
            self.assertTrue(instances_page.is_instance_present(instance))

        nonexistent_instance_name = "{0}_test".format(self.INSTANCE_NAME)
        instances_page.instances_table.filter(nonexistent_instance_name)
        self.assertEqual(instances_page.instances_table.rows, [])
        instances_page.instances_table.filter('')


class TestAdminInstancesPagination(helpers.AdminTestCase, TestInstances):
    INSTANCE_NAME = helpers.gen_random_resource_name('instance',
                                                     timestamp=False)
    ITEMS_PER_PAGE = 1
    INSTANCE_COUNT = 2

    @property
    def instances_page(self):
        self.home_pg.go_to_admin_overviewpage()
        return self.home_pg.go_to_admin_compute_instancespage()

    def setUp(self):
        super().setUp()
        self.instance_list = ["{0}-{1}".format(self.INSTANCE_NAME, item)
                              for item in range(1, self.INSTANCE_COUNT + 1)]

        # we have to use the project page, since admin has no create button
        instances_page = self.home_pg.go_to_project_compute_instancespage()

        # delete any old instances
        garbage = instances_page.instances_table.get_column_data(
            name_column='Instance Name')
        if garbage:
            instances_page.delete_instances(garbage)
            self.assertEqual(
                instances_page.find_messages_and_dismiss(), {messages.INFO})
            self.assertTrue(
                instances_page.are_instances_deleted(garbage))

        instances_page.create_instance(self.INSTANCE_NAME,
                                       instance_count=self.INSTANCE_COUNT)
        self.assertEqual(
            instances_page.find_messages_and_dismiss(), {messages.INFO})
        self.assertTrue(
            instances_page.is_instance_active(self.instance_list[1]))

        settings_page = self.home_pg.go_to_settings_usersettingspage()
        settings_page.change_pagesize(self.ITEMS_PER_PAGE)
        self.assertEqual(
            settings_page.find_messages_and_dismiss(), {messages.SUCCESS})

        def cleanup():
            settings_page = self.home_pg.go_to_settings_usersettingspage()
            settings_page.change_pagesize()
            self.assertEqual(
                settings_page.find_messages_and_dismiss(), {messages.SUCCESS})

            instances_page = self.instances_page
            instances_page.delete_instances(self.instance_list)
            self.assertEqual(
                instances_page.find_messages_and_dismiss(), {messages.INFO})
            self.assertTrue(
                instances_page.are_instances_deleted(self.instance_list))

        self.addCleanup(cleanup)

    def test_instances_pagination(self):
        """This test checks instance pagination

        Steps:
        1) Login to Horizon Dashboard as admin
        2) Navigate to user settings page
        3) Change 'Items Per Page' value to 1
        4) Go to Project > Compute > Instances page
        5) Create 2 instances
        6) Go to Admin > Compute > Instances page
        7) Check that only 'Next' link is available, only one instance is
           available (and it has correct name) on the first page
        8) Click 'Next' and check that on the second page only one instance is
           available (and it has correct name), there is no 'Next' link on page
        9) Go to user settings page and restore 'Items Per Page'
        10) Delete created instances via proper page
        """
        first_page_definition = {'Next': True, 'Prev': False,
                                 'Count': self.ITEMS_PER_PAGE,
                                 'Names': [self.instance_list[1]]}
        second_page_definition = {'Next': False, 'Prev': True,
                                  'Count': self.ITEMS_PER_PAGE,
                                  'Names': [self.instance_list[0]]}

        instances_page = self.instances_page
        instances_page.instances_table.assert_definition(
            first_page_definition, sorting=True)

        instances_page.instances_table.turn_next_page()
        instances_page.instances_table.assert_definition(
            second_page_definition, sorting=True)

        instances_page = self.instances_page
        instances_page.instances_table.assert_definition(
            first_page_definition, sorting=True)

    def test_instances_pagination_and_filtration(self):
        """This test checks instance pagination and filtration

        Steps:
        1) Login to Horizon Dashboard as admin
        2) Go to to user settings page
        3) Change 'Items Per Page' value to 1
        4) Go to Project > Compute > Instances page
        5) Create 2 instances
        6) Go to Admin > Compute > Instances page
        7) Check filter by Name of the first and the second instance in order
           to have one instance in the list (and it should have correct name)
           and no 'Next' link is available
        8) Check filter by common part of Name of in order to have one instance
           in the list (and it should have correct name) and 'Next' link is
           available on the first page and is not available on the second page
        9) Go to user settings page and restore 'Items Per Page'
        10) Delete created instances via proper page

        """
        first_page_definition = {'Next': True, 'Prev': False,
                                 'Count': self.ITEMS_PER_PAGE,
                                 'Names': [self.instance_list[1]]}
        second_page_definition = {'Next': False, 'Prev': False,
                                  'Count': self.ITEMS_PER_PAGE,
                                  'Names': [self.instance_list[0]]}
        filter_first_page_definition = {'Next': False, 'Prev': False,
                                        'Count': self.ITEMS_PER_PAGE,
                                        'Names': [self.instance_list[1]]}

        instances_page = self.instances_page
        instances_page.instances_table.set_filter_value('name')
        instances_page.instances_table.filter(self.instance_list[1])
        instances_page.instances_table.assert_definition(
            filter_first_page_definition, sorting=True)

        instances_page.instances_table.filter(self.instance_list[0])
        instances_page.instances_table.assert_definition(
            second_page_definition, sorting=True)

        instances_page.instances_table.filter(self.INSTANCE_NAME)
        instances_page.instances_table.assert_definition(
            first_page_definition, sorting=True)
        instances_page.instances_table.filter('')
