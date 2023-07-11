# Networking-2-slicing

## Introduction
The goal of the project is to implement a network slicing to enable dynamic activaton and deactivation of network slicing through both a GUI and CLI, considering the needs of the network. Three modes are implemented (```Work```, ```Gaming```, ```Emergency```).

The topology is composed by
- 1 SDN controller (```c1```)
- 5 OpenFlow switches (```s1```, ```s2```, ```s3```, ```s4```, ```s5```)
- 9 Hosts (```h1```, ```h2```, ```h3```, ```h4```, ```h5```, ```ps```, ```g1```, ```g2```, ```gs```)

## Project Description
Depending on the mode selected the bandwidth is divided between the slice

```IMPORTANT! A blue linkage means that the host is disconnected from the network```

### Work mode
While in ```work mode``` every connection between Gaming and Work is severed, with the exception of h5 which should connect with all the hosts excluding gs, meaning that 
- h1-h5 will be connected each other at 100Mbit/sec
- g1, g2, gs will be connected each other at 30Mbit/sec
- h5 will be connected with g1 and g2 at 20Mbit/sec
- h1-g5 will be connected with ps at 80Mbit/sec

![image](images/Work.png)

#### Test

Inserire test in work mode (CLI e GUI)
![image](images/pingall_work.png)

### Gaming mode
While in ```gaming mode``` only ps is disconnected from the network

![image](images/Gaming.png)

#### Test

Inserire test in gaming mode (CLI e GUI)


### Emergency mode
While in ```emergency mode``` only h1-h5 and ps are connected

![image](images/Emergency.png)

#### Test

Inserire test in emergency mode (CLI e GUI)

## How to run
1. Connect with a comnetsemu portale or install all the functionalities in your system
2. Launch the controller  
```$ sudo ryu-manager controller.py```
3. To run the program with the GUI launch
```$ python3 gui.py```
4. Emulate the topology with mininet
```$ sudo python3 topology.py```
5. To verify that all the links are working execute 
```mininet> pingall 0.1```

```IMPORTANT! Remember to delete the topology when you exit mininet, through the commands```

```
mininet> exit
$ sudo mn -c
```

### Useful command 
```mininet> dpctl dump-flows``` -> Show all the switches flows

```mininet> h1 ping h2``` (It also works with other hosts) 

```mininet> iperf h1 h2``` -> Verify the bandwidth of the linkage between two hosts (It also works with other hosts)

```mininet> net``` -> Shows all the hosts

```mininet> ports``` -> Shows all switches and their linkage with the hosts


## Presentation
[Project presentations]()

## Acknowledgment
Students: [Marco Zanon](https://github.com/marco-zan) - [Giuseppe Ostacchini](https://github.com/beppeosta) - [Luca Checchin](https://github.com/Kayser9)

Project for the course "Networking II - Softwarized and Virtualized Networks" 2022/2023 - [
Fabrizio Granelli](https://webapps.unitn.it/du/it/Persona/PER0003067/Curriculum)


<img src="https://user-images.githubusercontent.com/101217680/231458391-f247b1ba-2c5b-474d-ad5f-a40939d57d3d.png" width=30% height=30%>
