#!/bin/bash

    #andata

sudo ovs-ofctl add-flow s1 ip,priority=65500,in_port=3,nw_dst=10.0.0.9,idle_timeout=0,actions=output:1,normal
sudo ovs-ofctl add-flow s2 ip,priority=65500,in_port=1,nw_dst=10.0.0.9,idle_timeout=0,actions=output:2,normal
sudo ovs-ofctl add-flow s5 ip,priority=65500,in_port=1,nw_dst=10.0.0.9,idle_timeout=0,actions=output:3,normal


    #ritorno 

sudo ovs-ofctl add-flow s1 ip,priority=65500,in_port=3,nw_dst=10.0.0.1,idle_timeout=0,actions=output:1,normal
sudo ovs-ofctl add-flow s2 ip,priority=65500,in_port=2,nw_dst=10.0.0.1,idle_timeout=0,actions=output:1,normal
sudo ovs-ofctl add-flow s5 ip,priority=65500,in_port=1,nw_dst=10.0.0.1,idle_timeout=0,actions=output:3,normal
