'''
Created on 9 Sep 2014

@author: Tom Carroll
'''
from actuator import InfraSpec, MultiComponent, MultiComponentGroup, ctxt
from actuator.provisioners.openstack.components import (Server, Network, Subnet,
                                                         FloatingIP, Router,
                                                         RouterGateway, RouterInterface)

class SingleOpenstackServer(InfraSpec):
  server = Server("actuator1", "Ubuntu 13.10", "m1.small", nics=[ctxt.infra.net])
  net = Network("actuator_ex1_net")
  fip = FloatingIP("actuator_ex1_float", ctxt.infra.server,
                   ctxt.infra.server.iface0.addr0, pool="external")
  subnet = Subnet("actuator_ex1_subnet", ctxt.infra.net, "192.168.23.0/24",
                  dns_nameservers=['8.8.8.8'])
  router = Router("actuator_ex1_router")
  gateway = RouterGateway("actuator_ex1_gateway", ctxt.infra.router, "external")
  rinter = RouterInterface("actuator_ex1_rinter", ctxt.infra.router, ctxt.infra.subnet)
  

class MultipleServers(InfraSpec):
  #
  #First, declare the common networking components
  #
  net = Network("actuator_ex2_net")
  subnet = Subnet("actuator_ex2_subnet", ctxt.infra.net, "192.168.23.0/24",
                  dns_nameservers=['8.8.8.8'])
  router = Router("actuator_ex2_router")
  gateway = RouterGateway("actuator_ex2_gateway", ctxt.infra.router, "external")
  rinter = RouterInterface("actuator_ex2_rinter", ctxt.infra.router, ctxt.infra.subnet)
  #
  #now declare the "foreman"; this will be the only server the outside world can
  #reach, and it will pass off work requests to the workers. It will need a
  #floating ip for the outside world to see it
  #
  foreman = Server("foreman", "Ubuntu 13.10", "m1.small", nics=[ctxt.infra.net])
  fip = FloatingIP("actuator_ex2_float", ctxt.infra.server,
                   ctxt.infra.server.iface0.addr0, pool="external")
  #
  #finally, declare the workers MultiComponent
  #
  workers = MultiComponent(Server("worker", "Ubuntu 13.10", "m1.small",
                                  nics=[ctxt.infra.net]))
  
  
class MultipleGroups(InfraSpec):
  #
  #First, declare the common networking components
  #
  net = Network("actuator_ex3_net")
  subnet = Subnet("actuator_ex3_subnet", ctxt.infra.net, "192.168.23.0/24",
                  dns_nameservers=['8.8.8.8'])
  router = Router("actuator_ex3_router")
  gateway = RouterGateway("actuator_ex3_gateway", ctxt.infra.router, "external")
  rinter = RouterInterface("actuator_ex3_rinter", ctxt.infra.router, ctxt.infra.subnet)
  #
  #now declare the "foreman"; this will be the only server the outside world can
  #reach, and it will pass off work requests to the leaders of clusters. It will need a
  #floating ip for the outside world to see it
  #
  foreman = Server("foreman", "Ubuntu 13.10", "m1.small", nics=[ctxt.infra.net])
  fip = FloatingIP("actuator_ex3_float", ctxt.infra.server,
                   ctxt.infra.server.iface0.addr0, pool="external")
  #
  #finally, declare a "cluster"; a leader that coordinates the workers in the
  #cluster, which operate under the leader's direction
  #
  cluster = MultiComponentGroup("cluster",
                                leader=Server("leader", "Ubuntu 13.10", "m1.small",
                                              nics=[ctxt.infra.net]),
                                workers=MultiComponent(Server("cluster_node",
                                                              "Ubuntu 13.10",
                                                              "m1.small",
                                                              nics=[ctxt.infra.net])))
  