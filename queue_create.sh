#!/bin/bash

echo ' ---------------------------------------------- '
echo 'Switch 2: creating two queues on port 2:'
sudo ovs-vsctl set port s2-eth2 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=100000000 \
queues:252=@1q \
queues:251=@2q -- \
--id=@1q create queue other-config:min-rate=1000000 other-config:max-rate=10000000 -- \
--id=@2q create queue other-config:min-rate=1000000 other-config:max-rate=90000000
echo ' '



echo ' ---------------------------------------------- '
echo 'Switch 5: creating two queues on port 1:'
sudo ovs-vsctl set port s5-eth1 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=100000000 \
queues:522=@1q \
queues:521=@2q -- \
--id=@1q create queue other-config:min-rate=1000000 other-config:max-rate=10000000 -- \
--id=@2q create queue other-config:min-rate=1000000 other-config:max-rate=90000000
echo ' '


echo ' ---------------------------------------------- '
echo 'Switch 5: creating one queue on port 2:'
sudo ovs-vsctl set port s5-eth2 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=10000000 \
queues:54=@1q -- \
--id=@1q create queue other-config:min-rate=1000000 other-config:max-rate=10000000
echo ' '


echo ' ---------------------------------------------- '
echo 'Switch 4: creating one queue on port 1:'

sudo ovs-vsctl set port s4-eth2 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=10000000 \
queues:45=@1q -- \
--id=@1q create queue other-config:min-rate=1000000 other-config:max-rate=10000000
echo ' '

echo 'ottimo s1-eth1'
sudo ovs-vsctl set port s1-eth1 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=100000000 \

echo 'ottimo s1-eth2'
sudo ovs-vsctl set port s1-eth2 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=10000000 \

echo 'ottimo s1-eth3'
sudo ovs-vsctl set port s1-eth3 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=100000000 \

echo 'ottimo s1-eth4'
sudo ovs-vsctl set port s1-eth4 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=100000000 \

echo 'ottimo s1-eth5'
sudo ovs-vsctl set port s1-eth5 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=100000000 \


echo 'ottimo s2-eth1'
sudo ovs-vsctl set port s2-eth1 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=100000000 \

echo 'ottimo s2-eth3'
sudo ovs-vsctl set port s2-eth3 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=100000000 \

echo 'ottimo s2-eth4'
sudo ovs-vsctl set port s2-eth4 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=100000000 \


echo 'ottimo s3-eth1'
sudo ovs-vsctl set port s3-eth1 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=100000000 \

echo 'ottimo s3-eth2'
sudo ovs-vsctl set port s3-eth2 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=10000000 \

echo 'ottimo s3-eth3'
sudo ovs-vsctl set port s3-eth3 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=100000000 \

echo 'ottimo s3-eth4'
sudo ovs-vsctl set port s3-eth4 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=100000000 \

echo 'ottimo s3-eth5'
sudo ovs-vsctl set port s3-eth5 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=100000000 \



echo 'ottimo s4-eth1'
sudo ovs-vsctl set port s4-eth1 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=10000000 \

echo 'ottimo s4-eth3'
sudo ovs-vsctl set port s4-eth3 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=10000000 \

echo 'ottimo s4-eth4'
sudo ovs-vsctl set port s4-eth4 qos=@newqos -- \
--id=@newqos create QoS type=linux-htb \
other-config:max-rate=100000000 \


