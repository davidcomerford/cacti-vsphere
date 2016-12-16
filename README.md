

Dependencies
===========
python >= 2.6.6

pyvmomi

gcc


Install prequisities
====================
yum install gcc

yum install python-pip

pip install pyvmomi

pip install requests[security]

How is works
===========
Gathering data from vCenter isn't the fastest thing in the world so rather than slowing down Cacti's poller we're use the followoing approach.

1. Create a CRON job for vsphere-cluster-stats.py. Personally I run it every hours as the Cacti user.

2. Configure vCenter hostname and login details in $CACTI-HOME/scripts/vsphere.conf

3. Write the gathered data in JSON format to a file: /tmp/cacti-$VCENTER_HOSTNAME-cluster-stats.json

4. ss_vsphere_clusters.php is run by Cacti's script server and grabs the values from the JSON file. 

5. $CACTI-HOME/query_vsphere_clusters.xml defines the query for Cacti to run


Cacti man page
==============
http://docs.cacti.net/manual:088:3a_advanced_topics.3d_script_data_query_walkthrough#script_data_query_walkthrough

Create the XML description file
Script the data collecting script

1. Create Data Query
2. Create graph template
3. Associate Graph Template with Data Query
