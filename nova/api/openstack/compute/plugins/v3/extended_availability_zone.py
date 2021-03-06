# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Netease, LLC.
# All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

"""The Extended Availability Zone Status API extension."""

from nova.api.openstack import extensions
from nova.api.openstack import wsgi
from nova.api.openstack import xmlutil
from nova import availability_zones as avail_zone

ALIAS = "os-extended-availability-zone"
authorize = extensions.soft_extension_authorizer('compute',
                                                 'v3:' + ALIAS)


class ExtendedAZController(wsgi.Controller):
    def _extend_server(self, context, server, instance):
        key = "%s:availability_zone" % ExtendedAvailabilityZone.alias
        az = avail_zone.get_instance_availability_zone(context, instance)
        if not az and instance.get('availability_zone'):
            # Likely hasn't reached a viable compute node yet so give back the
            # desired availability_zone that *may* exist in the instance
            # record itself.
            az = instance['availability_zone']
        server[key] = az

    @wsgi.extends
    def show(self, req, resp_obj, id):
        context = req.environ['nova.context']
        if authorize(context):
            resp_obj.attach(xml=ExtendedAZTemplate())
            server = resp_obj.obj['server']
            db_instance = req.get_db_instance(server['id'])
            self._extend_server(context, server, db_instance)

    @wsgi.extends
    def detail(self, req, resp_obj):
        context = req.environ['nova.context']
        if authorize(context):
            resp_obj.attach(xml=ExtendedAZsTemplate())
            servers = list(resp_obj.obj['servers'])
            for server in servers:
                db_instance = req.get_db_instance(server['id'])
                self._extend_server(context, server, db_instance)


class ExtendedAvailabilityZone(extensions.V3APIExtensionBase):
    """Extended Server Attributes support."""

    name = "ExtendedAvailabilityZone"
    alias = ALIAS
    namespace = ("http://docs.openstack.org/compute/ext/"
                 "extended_availability_zone/api/v3")
    version = 1

    def get_controller_extensions(self):
        controller = ExtendedAZController()
        extension = extensions.ControllerExtension(self, 'servers', controller)
        return [extension]

    def get_resources(self):
        return []


def make_server(elem):
    elem.set('{%s}availability_zone' % ExtendedAvailabilityZone.namespace,
             '%s:availability_zone' % ExtendedAvailabilityZone.alias)


class ExtendedAZTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('server', selector='server')
        make_server(root)
        alias = ExtendedAvailabilityZone.alias
        namespace = ExtendedAvailabilityZone.namespace
        return xmlutil.SlaveTemplate(root, 1, nsmap={alias: namespace})


class ExtendedAZsTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('servers')
        elem = xmlutil.SubTemplateElement(root, 'server', selector='servers')
        make_server(elem)
        alias = ExtendedAvailabilityZone.alias
        namespace = ExtendedAvailabilityZone.namespace
        return xmlutil.SlaveTemplate(root, 1, nsmap={alias: namespace})
