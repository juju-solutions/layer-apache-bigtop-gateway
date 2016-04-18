from charms.reactive import when, when_not, is_state, set_state, remove_state
from charms.layer.apache_bigtop_base import Bigtop, get_layer_opts
from charmhelpers.core import host, hookenv
from charms import layer


@when_not('components.installed')
def report_status():
    nn_joined = is_state('namenode.joined')
    rm_joined = is_state('resourcemanager.joined')
    if not nn_joined and not rm_joined:
        hookenv.status_set('blocked', 'waiting for connections to resource manager and namenode')
    elif not nn_joined:
        hookenv.status_set('blocked', 'waiting for connection to namenode')
    elif not rm_joined:
        hookenv.status_set('blocked', 'waiting for connection to resource manager')


@when('namenode.joined', 'resourcemanager.joined', 'puppet.available')
@when_not('components.installed')
def install_component(namenode, resourcemanager):
    '''Install only if nn and rm have sent their FQDNs.'''
    if namenode.namenodes() and resourcemanager.resourcemanagers():
        set_state('components.installed')
        options = layer.options('apache-bigtop-base')
        components = options.get("bigtop_component_list")
        hookenv.status_set('maintenance', 'installing {}'.format(components))
        nn_fqdn = namenode.namenodes()[0]
        rm_fqdn = resourcemanager.resourcemanagers()[0]
        bigtop = Bigtop()
        hosts = {'namenode': nn_fqdn, 'resourcemanager': rm_fqdn}
        bigtop.install_component(RM=rm_fqdn, NN=nn_fqdn)
        for component in components.split():
            try:
                for port in get_layer_opts().exposed_ports(component):
                    hookenv.open_port(port)
            except AttributeError:
                hookenv.log("Not opening ports for component {}".format(component))
        hookenv.status_set('active', 'ready')
    else:
        hookenv.status_set('waiting',
                           'waiting for namenode and resource manager to become ready')


@when_not('namenode.joined')
def namenode_departed():
    remove_state('components.installed')


@when_not('resourcemanager.joined')
def resourcemrg_departed():
    remove_state('components.installed')
