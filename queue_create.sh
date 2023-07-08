#!/bin/bash

echo ' ---------------------------------------------- '
echo 'Switch 2: creating two queues on port 2:'
sudo ovs-vsctl set port s2-eth2 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=10000000 \
queues:123=@1q \
queues:234=@2q -- \
--id=@1q create queue other-config:min-rate=10000000 other-config:max-rate=500000000 -- \
--id=@2q create queue other-config:min-rate=10000000 other-config:max-rate=500000000 
echo ' '



echo ' ---------------------------------------------- '
echo 'Switch 5: creating two queues on port 1:'
sudo ovs-vsctl set port s5-eth1 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=1000000000 \
queues:123=@1q \
queues:234=@2q -- \
--id=@1q create queue other-config:min-rate=100000000 other-config:max-rate=500000000 -- \
--id=@2q create queue other-config:min-rate=100000000 other-config:max-rate=500000000 
echo ' '