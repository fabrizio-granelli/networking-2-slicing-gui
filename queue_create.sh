#!/bin/bash

echo ' ---------------------------------------------- '
echo 'Switch 2: creating two queues on port 2:'
sudo ovs-vsctl set port s2-eth2 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=10000000 \
queues:251=@1q \
queues:252=@2q -- \
--id=@1q create queue other-config:min-rate=10000000 other-config:max-rate=800000000 -- \
--id=@2q create queue other-config:min-rate=10000000 other-config:max-rate=200000000 
echo ' '



echo ' ---------------------------------------------- '
echo 'Switch 5: creating two queues on port 1:'
sudo ovs-vsctl set port s5-eth1 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=1000000000 \
queues:521=@1q \
queues:522=@2q \
queues:54=@3q -- \
--id=@1q create queue other-config:min-rate=100000000 other-config:max-rate=800000000 -- \
--id=@2q create queue other-config:min-rate=100000000 other-config:max-rate=200000000 -- \
--id=@3q create queue other-config:min-rate=100000000 other-config:max-rate=200000000 \

echo ' '




echo ' ---------------------------------------------- '
echo 'Switch 4: creating one queue on port 1:'
sudo ovs-vsctl set port s5-eth1 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=1000000000 \
queues:45=@1q -- \
--id=@1q create queue other-config:min-rate=100000000 other-config:max-rate=200000000 
echo ' '
