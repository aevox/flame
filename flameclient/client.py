# -*- coding: utf-8 -*-

# This software is released under the MIT License.
#
# Copyright (c) 2014 Cloudwatt
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from flameclient.flame import TemplateGenerator  # noqa
from flameclient.managers import KeystoneManager

from keystoneclient.openstack.common.apiclient.exceptions import Conflict


class Client(object):
    """Flame client.

    This client is a context.
    Example:
        with Client(...) as flame:
            flame.foo(bar)

    :param string username: A user name with access to the project.
    :param string password: The user's password.
    :param string tenant_name: Name of project to use for authentication.
    :param string auth_url: Authentication URL.

    Optional parameters:
    :param boolean insecure :Explicitly allow clients to perform
        \"insecure\" SSL (https) requests. The server's certificate will
        not be verified against any certificate authorities. This option
        should be used with caution.
    :param string endpoint_type: Type of endpoint to use.
    :param string region_name: Region Name to use.
    :param string target_projet: Name of project to extract template from.
        If the user is not admin in that project, it will grant itself
        admin role for the operation. Defaults to tenant_name. User must
        be admin.
    """
    def __init__(self, username, password, tenant_name, auth_url, **kwargs):
        self.username = username
        self.password = password
        self.tenant_name = tenant_name
        self.auth_url = auth_url
        self.target_project = kwargs.get('target_project')
        self.endpoint_type = kwargs.get('endpoint_type', 'publicURL')
        self.region_name = kwargs.get('region_name', None)
        self.insecure = kwargs.get('insecure', False)
        self.set_as_admin = False

        if self.target_project:
            self.key_mgr = KeystoneManager(self.username, self.password,
                                           self.tenant_name, self.auth_url,
                                           self.insecure)
            self.target_project_id = self.key_mgr.get_target_project_id(
                self.target_project)
            try:
                self.key_mgr.become_project_admin(self.target_project_id)
                self.set_as_admin = True
            # Execption raised if user is already admin.
            except Conflict:
                self.set_as_admin = False
        else:
            self.target_project = self.tenant_name
        self.template_generator = TemplateGenerator(
            self.username, self.password,
            self.target_project, self.auth_url,
            region_name=self.region_name,
            insecure=self.insecure,
            endpoint_type=self.endpoint_type)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.set_as_admin:
            self.key_mgr.undo_become_project_admin(self.target_project_id)

    def extract_vm_details(self, exclude_servers=False, exclude_volumes=False,
                           generate_stack_data=False, exclude_keypairs=False,
                           **kwargs):
        return self.template_generator.extract_vm_details(exclude_servers,
                                                          exclude_volumes,
                                                          exclude_keypairs,
                                                          generate_stack_data,
                                                          **kwargs)

    def extract_data(self):
        return self.template_generator.extract_data()

    def heat_template(self):
        return self.template_generator.heat_template()

    def stack_data_template(self):
        return self.template_generator.stack_data_template()
