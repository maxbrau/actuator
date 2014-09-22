actuator
========

Actuator allows you to use Python to declaratively describe system infra, configuration, and execution requirements, and then provision them in the cloud.

1. [Intro](#intro)
2. [Requirements](#requirements)
  1. [Python version](#python)
  2. [Core packages](#core)
  3. [Cloud support](#cloud)
  4. [Testing with nose](#testing)
3. [Overview](#overview) (as close to a tl;dr that's still meaningful)
  1. [Infra Model](#ov_inframodel)
  2. [Namespace Model](#ov_namespacemodel)
  3. [Configuration Model](#ov_configmodel)
  4. [Execution Model](#ov_execmodel)
4. [Infra Models](#inframodels)
  1. [A simple Openstack example](#simple_openstack_example)
  2. [Multiple Components](#multi_components)
  3. [Component Groups](#component_groups)
5. [Namespace Models](#nsmodels)
6. Configuration Models
7. Execution Models
8. Roadmap

## <a name="intro">Intro</a>
**Current status**
- **10 Sep 2014:** actuator can provision a limited set of items against Openstack clouds. It can create instances, networks, subnets, routers (plus router gateways and interfaces), and floating IPs. Not all options available via the Python Openstack client libraries are supported for each provisionable.

Actuator seeks to provide an end-to-end set of tools for spinning up systems in the cloud, from provisioning the infra, defining the names that govern operation, configuring the infra for the software that is to be run, and then executing that system's code on the configured infra.

It does this by providing facilities that allow a system to be described as a collection of *models* in a declarative fashion directly in Python code, in a manner similar to various declarative systems for ORMs (Elixir being a prime example). Being in Python, these models:

- can be very flexible and dynamic in their composition
- can be integrated with other Python packages
- can be authored and browsed in existing IDEs
- can be debugged with standard tools
- can be used in a variety of ways
- and can be factored into multiple modules of reusable sets of declarative components

And while each model provides capabilties on their own, they can be inter-related to not only exchange information, but to allow instances of a model to tailor the content of other models.

Actuator uses a Python *class* as the basis for defining a model, and the class serves as a logical description of the item being modeled; for instance a collection of infrastructure components for a system. These model classes can have both static and dynamic aspects, and can themselves be easily created within a factory function to make the classes' content highly variable.

Actuator models can be related to each other so that their structure and data can inform and sometimes drive the content of other models.

## <a name="requirements">Requirements</a>
###<a name="python">Python version</a>

Actuator has been developed against Python 2.7. Support for 3.x will come later.

###<a name="core">Core packages</a>

Actuator requires the following packages:

  - [networkx](https://pypi.python.org/pypi/networkx), 1.9 minimum
  - [faker](https://pypi.python.org/pypi/fake-factory) (to support running tests), 0.4.2 minimum

###<a name="cloud">Cloud support</a>

Cloud support modules are only required for the cloud systems you wish to provision against

####Openstack
  - [python-novaclient](https://pypi.python.org/pypi/python-novaclient), 2.18.1 minimum
  - [python-neutronclient](https://pypi.python.org/pypi/python-neutronclient), 2.3.7 minimum
  - [ipaddress](https://pypi.python.org/pypi/ipaddress), 1.0.6 minimum

###<a name="testing">Testing with nose</a>
  - [nose](https://pypi.python.org/pypi/nose)
  - [coverage](https://pypi.python.org/pypi/coverage)

## <a name="overview">Overview</a>

Actuator splits the modeling space into four parts:

###<a name="ov_inframodel">Infra Model</a>

The *infra model*, established with a subclass of **InfraSpec**, defines all the cloud-provisionable infrastructure components of a system and their inter-relationships. Infra models can have fixed components that are always provisioned with each instance of the model class, as well as variable components that allow multiple copies of components to be easily created on an instance by instance basis. The infra model also has facilities to define groups of components that can be created as a whole, and an arbitrary number of copies of these groups can be created for each instance. References into the infra model can be held by other models, and these references can be subsequently evaluated against an instance of the infra model to extract data from that particular instance. For example, a namespace model may need the IP address from a particular server in an infra model, and so the namespace model may hold a reference into the infra model for the IP address attribute that yields the actual IP address of a provisioned server when an instance of that infra model is provisioned.

###<a name="ov_namespacemodel">Namespace Model</a>

The *namespace model*, established with a subclass of **NamespaceSpec**, defines a hierarchical namespace which defines all the names that are important to the run-time components of a system. Names in the namespace can be used for a variety of purposes, such as setting up environment variables, or establishing name-value pairs for processing template files such as scripts or properties files. The names in the namespace are organized into system components which map onto the executable software in a system, and each system component's namespace is composed of any names specific to that component, plus the names that are defined higher up in the namespace hierarchy. Values for the names can be baked into the model, supplied at model class instantiation, by setting values on the model class instnace, or can be acquired by resolving references to other models such as the infra model.

###<a name="ov_configmodel">Configuration Model</a>

The *configuration model*, established with a subclass of **ConfigSpec**, defines all the tasks to perform on the system components' infrastructure that make them ready to run the system's executables. The configuration model defines tasks to be performed on the logical system components of the namespace model, which in turn inidicates what infrastructure is involved in the configuration tasks. The configuration model also captures task dependencies so that the configuration tasks are all performed in the proper order.

###<a name="ov_execmodel">Execution Model</a>

The *execution model*, established with a subclass of **ExecutionSpec**, defines the actual processes to run for each system component named in the namespace model. Like with the configuration model, dependencies between the executables can be expressed so that a particular startup order can be enforced.

Each model can be built and used independently, but it is the inter-relationships between the models that give actuator its representational power.

Actuator then provides a number of support objects that can take instances of these models and processes their informantion, turning it into actions in the cloud. So for instance, a provisioner can take an infra model instance and manage the process of provisioning the infra it describes, and another can marry that instance with a namespace to fully populate a namespace model instance so that the configurator can carry out configuration tasks, and so on.

As may have been guessed, the key model in actuator is the namespace model, as it serves as the focal point to tie all the other models together.

##<a name="inframodels">Infra models</a>

Although the namespace model is the one that is most central in actuator, it actually helps to start with the infra model as it not only is a little more accessible, but building an infra model first can yield immediate benefits. The infra model describes all the dynmaically provisionable infra components and describes how they relate to each other. The model can define groups of components and components that can be repeated an arbitrary number of times, allowing them to be nested in very complex configurations.

### <a name="simple_openstack_example">A simple Openstack example</a>
The best place to start is to develop a model that can be used provision the infrastructure for a system. An infrastructure model is defined by creating a class that describes the infra in a declarative fashion. This example will use components built the [Openstack](http://www.openstack.org/) binding to actuator.

```python
from actuator import InfraSpec, ctxt
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
```

The order of the components in the class isn't particularly important; the provisioner will take care of sorting out what needs to be done before what. Also note the use of 'ctxt.infra.*' for some of the arguments; this is how actuator defers evaluation of an argument until the needed reference is defined.

Instances of the class (and hence the model) are then created, and the instance is given to a provisioner which inspects the model instance and performs the necessary provsioning actions in the proper order.

```python
from actuator.provisioners.openstack.openstack import OpenstackProvisioner
inst = SingleOpenstackServer("actuator_ex1")
provisioner = OpenstackProvisioner(uid, pwd, uid, url)
provisioner.provision_infra_spec(inst)
```

Often, there's a lot of repeated boilerplate in an infra spec; in the above example the act of setting up a network, subnet, router, gateway, and router interface are all common steps to get access to provisioned infra from outside the cloud. Actuator provides two ways to factor out common component groups: providing a dictionary of components to the with_infra_components function, and using the [ComponetGroup](#component_groups) wrapper class to define a group of standard components. We'll recast the above example using with_infra_components():

```python
gateway_components = {"net":Network("actuator_ex1_net"),
                      "subnet":Subnet("actuator_ex1_subnet", ctxt.infra.net,
                                      "192.168.23.0/24", dns_nameservers=['8.8.8.8']),
                      "router":Router("actuator_ex1_router"),
                      "gateway":RouterGateway("actuator_ex1_gateway", ctxt.infra.router,
                                              "external")
                      "rinter":RouterInterface("actuator_ex1_rinter", ctxt.infra.router,
                                               ctxt.infra.subnet)}


class SingleOpenstackServer(InfraSpec):
  with_infra_components(**gateway_components)
  server = Server("actuator1", "Ubuntu 13.10", "m1.small", nics=[ctxt.infra.net])
  fip = FloatingIP("actuator_ex1_float", ctxt.infra.server,
                   ctxt.infra.server.iface0.addr0, pool="external")
```

With with_infra_components(), all the keys in the dictionary are established as attributes on the infra model class, and can be accessed just as if they were declared directly in the class. Since this is just standard keyword argument notation, you could also use a list of "name=value" expressions for the same effect.

### <a name="multi_components">Multiple components</a>
If you require a set of identical components to be created in a model, the MultiComponent wrapper provides a way to declare a component as a template and then to get as many copies of that template stamped out as required:

```python
from actuator import InfraSpec, MultiComponent, ctxt, with_infra_components
from actuator.provisioners.openstack.components import (Server, Network, Subnet,
                                                         FloatingIP, Router,
                                                         RouterGateway, RouterInterface)

class MultipleServers(InfraSpec):
  #
  #First, declare the common networking components with with_infra_components
  #
  with_infra_components(**gateway_components)
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
```

The *workers* MultiComponent works like a dictionary in that it can be accessed with a key. For every new key that is used with workers, a new instance of the template component is created:

```python
>>> inst2 = MultipleServers("two")
>>> len(inst2.workers)
0
>>> for i in range(5):
...     _ = inst2.workers[i]
...
>>> len(inst2.workers)
5
>>>
```

Keys are always coerced to strings, and for each new instance of the MultiComponent template that is created, the original name is appened with '_{key}' to make each instance distinct.

```python
>>> for w in inst2.workers.instances().values():
...     print w.logicalName
...
worker_1
worker_0
worker_3
worker_2
worker_4
>>>
```

### <a name="component_groups">Component Groups</a>

If you require a group of different resources to be provisioned as a unit, the ComponentGroup() wrapper provides a way to define a template of multiple resources that will be provisioned as a whole. The following example shows how the boilerplate gateway components could be expressed using a ComponentGroup().

```python
gateway_component = ComponentGroup("gateway", net=Network("actuator_ex1_net"),
                              subnet=Subnet("actuator_ex1_subnet", ctxt.comp.container.net,
                                          "192.168.23.0/24", dns_nameservers=['8.8.8.8']),
                              router=Router("actuator_ex1_router"),
                              gateway=RouterGateway("actuator_ex1_gateway", ctxt.comp.container.router,
                                                    "external")
                              rinter=RouterInterface("actuator_ex1_rinter", ctxt.comp.container.router,
                                                     ctxt.comp.container.subnet))


class SingleOpenstackServer(InfraSpec):
  gateway = gateway_component
  server = Server("actuator1", "Ubuntu 13.10", "m1.small", nics=[ctxt.infra.gateway.net])
  fip = FloatingIP("actuator_ex1_float", ctxt.infra.server,
                   ctxt.infra.server.iface0.addr0, pool="external")
```

The keyword args used in creating the ComponentGroup become the attributes of the instances of the group.

If you require a group of different resources to be provisioned together repeatedly, the MultiComponentGroup() wrapper provides a way to define a template of multiple resources that will be provioned together. MultiComponentGroup() is simply a shorthand for wrapping a ComponentGroup in a MultiComponent. The following model only uses Servers in the template, but any component can appear in a MultiComponentGroup.

```python
from actuator import InfraSpec, MultiComponent, MultiComponentGroup, ctxt
from actuator.provisioners.openstack.components import (Server, Network, Subnet,
                                                         FloatingIP, Router,
                                                         RouterGateway, RouterInterface)

class MultipleGroups(InfraSpec):
  #
  #First, declare the common networking components
  #
  with_infra_components(**gateway_components)
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
```

The keyword args used in creating the ComponentGroup become the attributes of the instances of the group; hence the following expressions are fine:

```python
>>> inst3 = MultipleGroups("three")
>>> len(inst3.cluster)
0
>>> for region in ("london", "ny", "tokyo"):
...     _ = inst3.cluster[region]
...
>>> len(inst3.cluster)
3
>>> inst3.cluster["ny"].leader.iface0.addr0
<actuator.infra.InfraModelInstanceReference object at 0x02A51970>
>>> inst3.cluster["ny"].workers[0]
<actuator.infra.InfraModelInstanceReference object at 0x02A56170>
>>> inst3.cluster["ny"].workers[0].iface0.addr0
<actuator.infra.InfraModelInstanceReference object at 0x02A561B0>
>>> len(inst3.cluster["ny"].workers)
1
>>>
```

This model will behave similarly to the MultiServer attribute in the previous model; that is, the *cluster* attribute can be treated like a dictionary and keys will cause a new instance of the MultiComponentGroup to be created. Note also that you can nest MultiComponents in MultiComponentGroups, and vice versa.


#### Model references
Once a model class has been defined, you can create expressions that refer to attributes of components in the class:

```python
>>> SingleOpenstackServer.server
<actuator.infra.InfraModelReference object at 0x0291CB70>
>>> SingleOpenstackServer.server.iface0
<actuator.infra.InfraModelReference object at 0x02920110>
>>> SingleOpenstackServer.server.iface0.addr0
<actuator.infra.InfraModelReference object at 0x0298C110>
>>>
```

Likewise, you can create references to attributes on instances of the model class:
```python
>>> inst.server
<actuator.infra.InfraModelInstanceReference object at 0x0298C6B0>
>>> inst.server.iface0
<actuator.infra.InfraModelInstanceReference object at 0x0298C6D0>
>>> inst.server.iface0.addr0
<actuator.infra.InfraModelInstanceReference object at 0x0298CAD0>
>>>
```

All of these expressions result in a reference object, either a model reference or a model instance reference. _References_ are objects that serve as a "pointer" to a component or attribute of an infra model. _Model references_ (or just "model references") are logical references into an infra model; there may not be an actual component or attribute underlying the reference. _Model instance references_ (or "instance references") are references into an instance of an infra model; they refer to an actual component or attribute (although the value of the attribute may not have been set yet). Instance references can only be created relative to an instance of a model, or by transforming a model reference to an instance reference with respect to an instance of a model. An example here will help:

```python
#re-using the definition of SingleOpenstackServer from above...
>>> inst = SingleOpenstackServer("refs")
>>> modref = SingleOpenstackServer.server
>>> instref = inst.server
>>> instref is inst.get_inst_ref(modref)
True
>>>
```

The ability to generate model references from an infra model and turn them into instance references against an instance of the model (which represent things to be provisioned) is key in actuator's ability to flexibly describe the components of a system's infra. In particular, we can use the namespace model to drive the infra required to support the logical components of the namespace.

## <a name="nsmodels">Namespace models</a>
The namespace model provides the means for joining the other actuator models together. It does this by declaring the logical components of a system, relating these components to the infrastructure elements where the components are to execute, and providing the means to identify what configuration task is to be carried out for each component as well as what executables are involved with making the component function.

A namespace model has four aspects. It provides for:

1. Capturing the logical execution components of a system
2. Capturing the relationship between logical components and hosts in the infra model where the components are to execute
3. The means to arrange the components in a meaningful hierarchy
4. The means to establish names within the hierachy whose values will impact configuration activities and the operation of the components

### An example
Here's a trivial example that demonstrates the basic features of a namespace. It will model two components, and app server and a computation engine, and use the SingleOpenstackServer infra model from above for certain values:

```python
from actuator import Var, NamespaceSpec, Component, with_variables

class SOSNamespace(NamespaceSpec):
  with_variables(Var("COMP_SERVER_HOST", SingleOpenstackServer.server.iface0.addr0),
                 Var("COMP_SERVER_PORT", '8081'),
                 Var("EXTERNAL_APP_SERVER_IP", SingleOpenstackServer.fip.ip),
                 Var("APP_SERVER_PORT", '8080'))
                 
  app_server = (Component("app_server", host_ref=SingleOpenstackServer.server)
                  .add_variable(Var("APP_SERVER_HOST", SingleOpenstackServer.server.iface0.addr0)))
                                
  compute_server = Component("compute_server", host_ref=SingleOpenstackServer.server)
```

First, some global Vars are established that capture the host and port where the compute_server will be found, the external IP where the app_server will be found, and the port number where it can be contacted. While the ports are hard coded values, the host IPs are determined from the SingleOpenstackServer model by supplying a model reference to the model attribute where the IP will become available. Since these Vars are defined at the model (global) level, they are visible to all components.

Next comes the app_server component, which is declared with a call to Component. Besides a name, the Component is supplied a host_ref in the form of Server model reference from the SingleOpenstackserver model. This tells the namespace that this component's configuration tasks and executables will be run on whatever host is provisioned for this part of the model. The app_server component is also supplied a  private Var object that captures the host IP where the server will run. While the app_server binds to an IP on the subnet, the FloatingIP associated with this subnet IP will enable the server to be reached from outside the subnet.

Finally, we declare the compute_server Component. Similar to the app_server Component, the compute_server Component identifies the Server where it will run by setting the host_ref keyword to a infra model reference for the Server to use.

When an instance of the namespace is created, useful questions can be posed to the instance:
* We can ask for a list of components
* We can ask for all the Vars (and their values) from the perspective of a specific component
* We can ask for any Vars whose value can't be resolved from the perspective of each component
* We can ask to compute the necessary provisioning based on the namespace and an infra model instance\]

That looks something like this:


### Var objects
Namespaces and their components serve as containers for *Var* objects. These objects provide a means to establish names that can be used symbolically for a variety of purposes, such as environment variables, 
