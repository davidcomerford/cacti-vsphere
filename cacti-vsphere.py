import atexit
import ssl
import os
import json
import sys, getopt
import ConfigParser
from pyVim.connect import SmartConnect, Disconnect
from pyVim import connect
from pyVmomi import vim
from pyVmomi import vmodl


"""
Variables - yay
"""
DEBUG = True
CONFIGPATH = '/var/www/html/cacti/scripts/'
CONFIGFILE = CONFIGPATH + 'vcenters.conf'
clusters = []
dumpfilepath = '/tmp/'

"""
Validate arguments
"""
if not len(sys.argv) < 2:
   hostarg = sys.argv[1]

else:
    print("Usage: %s vcenter-hostname" %sys.argv[0])
    sys.exit(1)

"""
Read config file
"""
if not os.path.isfile(CONFIGFILE):
    print "Could not open config file: %s " % CONFIGFILE
    sys.exit(1)
    
try:
    config = ConfigParser.ConfigParser()
    config.read(CONFIGFILE)
    hostname = config.get(hostarg, 'hostname')
    username = config.get(hostarg, 'username') 
    password = config.get(hostarg, 'password')
 
except ConfigParser.ParsingError, err:
    print 'Could not parse:', err
except ConfigParser.NoSectionError:
    print 'Could not find host: %s in config file: %s' % (hostarg,CONFIGFILE)
    sys.exit(1)

if DEBUG: print("%s @ %s with password: %s" % (username,hostname,password))

"""
Connect to vCenter
"""
if DEBUG: print("Connecting...")

sslContext = ssl.create_default_context()
sslContext.check_hostname = False
sslContext.verify_mode = ssl.CERT_NONE

try:
    service_instance = connect.SmartConnect(host=hostname, user=username, pwd=password,sslContext=sslContext)
    content = service_instance.RetrieveContent()
    atexit.register(connect.Disconnect, content)                                                                      
    if DEBUG: print("Connected")
except vmodl.MethodFault as error:
    print("Caught exception during connection: " + error.msg)
    sys.exit(1)
 
if DEBUG: print("Server time: %s") % service_instance.CurrentTime()
 
container = content.rootFolder 


def get_properties(content, viewType, props, specType):
    """
    Obtains a list of specific properties for a particular Managed Object Reference data object.
    This took far too long to learn.

    :param content: ServiceInstance Managed Object
    :param viewType: Type of Managed Object Reference that should populate the View
    :param props: A list of properties that should be retrieved for the entity
    :param specType: Type of Managed Object Reference that should be used for the Property Specification
    """
    
    # create an object spec to define the beginning of the traversal;
    # container view is the root object for this traversal
    objView = content.viewManager.CreateContainerView(content.rootFolder, viewType, True)
    
    # create a traversal spec to select all objects in the view
    tSpec = vim.PropertyCollector.TraversalSpec()
    tSpec.name = 'tSpecName'
    tSpec.path='view'
    tSpec.skip=False 
    tSpec.type=vim.view.ContainerView
    
    # specify the property for retrieval (virtual machine name)
    pSpec = vim.PropertyCollector.PropertySpec()
    pSpec.all = False
    pSpec.pathSet = props
    pSpec.type = specType
    
    # Create object specification to define the starting point of inventory navigation
    oSpec = vim.PropertyCollector.ObjectSpec()
    oSpec.obj = objView
    oSpec.selectSet = [tSpec]
    oSpec.skip = True
    
    # create a PropertyFilterSpec and add the object and property specs to it; 
    # use the getter method to reference the mapped XML representation of the lists and add the specs directly to the list
    pfSpec = vim.PropertyCollector.FilterSpec()
    pfSpec.objectSet = [oSpec]
    pfSpec.propSet = [pSpec]
    pfSpec.reportMissingObjectsInResults = False
    
    # get the data from the server
    retOptions = vim.PropertyCollector.RetrieveOptions()
    retProps = content.propertyCollector.RetrievePropertiesEx(specSet=[pfSpec], options=retOptions)
    
    totalProps = []
    totalProps += retProps.objects
    while retProps.token:
        retProps = content.propertyCollector.ContinueRetrievePropertiesEx(token=retProps.token)
        totalProps += retProps.objects
    
    # Destroy the view because it eats vCenter resources
    objView.Destroy()
    
    # Turn the output in retProps into a usable dictionary of values
    gpOutput = []
    for eachProp in totalProps:
        propDic = {}
        for prop in eachProp.propSet:
            propDic[prop.name] = prop.val
        propDic['moref'] = eachProp.obj
        gpOutput.append(propDic)

    return gpOutput


all = get_properties(content, [vim.ComputeResource], ['name','host'], vim.ComputeResource)
hostprops = get_properties(content, [vim.HostSystem], ['name','hardware.cpuInfo.numCpuCores'], vim.HostSystem)
vmprops = get_properties(content, [vim.VirtualMachine], ['runtime.host','config.name','config.hardware.numCPU','config.hardware.memoryMB','runtime.powerState'], vim.VirtualMachine)

masterlist = {}

# Counter for hostsystem core count
hostcorecount = 0

# VM core counter
vmcorecount = 0

# Counters for powered on and off VMs
oncount = 0
offcount = 0
     

for c in all:
    # CLUSTER SECTION
    if DEBUG: print "=== cluster %s ===" % c['moref'].name
    
    # HostSystem core count
    for h1 in c['host']:
        for h2 in hostprops:
            if h1 == h2['moref']:
                print("*")
                hostcorecount += h2['hardware.cpuInfo.numCpuCores']
        
    # VM property counts
    for h in c['host']:
        if DEBUG: print("Host: %s") % h.name               
                    
        for vm in vmprops:
            # VM SECTION
            if vm['runtime.host'] == h:
                name = vm['config.name']
                numCPU = vm['config.hardware.numCPU']
                memoryMB = vm['config.hardware.memoryMB'] 
                power = vm['runtime.powerState']
                
                if power == "poweredOn":
                    oncount +=1
                    vmcorecount += numCPU
                elif power == "poweredOff" or power == "suspended":
                    offcount +=1


    # Calculate pCPU:vCPU ratio
    cpuratio =  round(float(vmcorecount)/hostcorecount,2)
    masterlist[c['moref'].name] = {'cpuratio': cpuratio,'vmcorecount':vmcorecount, 'vmpoweredon': oncount, 'vmpoweredoff': offcount}
    if DEBUG: print masterlist
    
    # Reset the counters for the next cluster
    hostcorecount = 0
    oncount = 0
    offcount = 0

dumpfile = dumpfilepath + 'cacti-' + hostname + '-data.json'
if DEBUG: print("Dumping json to %s" %dumpfile)
with open(dumpfile, 'w') as outfile:
    json.dump(masterlist, outfile, sort_keys=True, indent=4, encoding="utf-8")
outfile.close()
    

Disconnect(c)
if DEBUG: print("Discoonected")
