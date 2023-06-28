import os
import shlex
import time

from subprocess import check_output

from comnetsemu.cli import CLI
from comnetsemu.net import Containernet, VNFManager
from comnetsemu.node import DockerHost
from mininet.link import TCLink
from mininet.log import info, setLogLevel

from mininet.topo import Topo
from mininet.node import OVSKernelSwitch, RemoteController
    
class NetworkSlicingTopo(Topo):
    def __init__(self):

        Topo.__init__(self)

        gig_net = { "bw": 1000 }
        megabit_net = { "bw": 100 }
        host_link_config = dict()
        
        h1 = self.addHost(
            "h1",
            cls=DockerHost,
            dimage="dev_test",
            ip="10.0.0.1/24",
            mac="00:00:00:00:00:01",
            docker_args={"hostname": "h1"}
        )
        h2 = self.addHost(
            "h2",
            cls=DockerHost,
            dimage="dev_test",
            ip="10.0.0.2/24",
            mac="00:00:00:00:00:02",
            docker_args={"hostname": "h2"}
        )
        h3 = self.addHost(
            "h3",
            cls=DockerHost,
            dimage="dev_test",
            ip="10.0.0.1/24",
            mac="00:00:00:00:00:01",
            docker_args={"hostname": "h3"}
        )
        h4 = self.addHost(
            "h4",
            cls=DockerHost,
            dimage="dev_test",
            ip="10.0.0.2/24",
            mac="00:00:00:00:00:02",
            docker_args={"hostname": "h4"}
        )
        h5 = self.addHost(
            "h5",
            cls=DockerHost,
            dimage="dev_test",
            ip="10.0.0.1/24",
            mac="00:00:00:00:00:01",
            docker_args={"hostname": "h5"}
        )
        g1 = self.addHost(
            "g1",
            cls=DockerHost,
            dimage="dev_test",
            ip="10.0.0.3/24",
            mac="00:00:00:00:00:03",
            docker_args={"hostname": "g2"}
        )

        g2 = self.addHost(
            "g2",
            cls=DockerHost,
            dimage="dev_test",
            ip="10.0.0.3/24",
            mac="00:00:00:00:00:03",
            docker_args={"hostname": "g2"}
        )
        ser1 = self.addHost(
            "ser1",
            cls=DockerHost,
            dimage="dev_test",
            ip="10.0.0.1/24",
            mac="00:00:00:00:00:01",
            docker_args={"hostname": "ser1"}
        )
        ser2 = self.addHost(
            "ser2",
            cls=DockerHost,
            dimage="dev_test",
            ip="10.0.0.1/24",
            mac="00:00:00:00:00:01",
            docker_args={"hostname": "ser2"}
        )

        
        switches = {}
        for i in range(5):
            sconfig = {"dpid": "%016x" % (i + 1)}
            switches["s" + str(i+1)] = self.addSwitch("s%d" % (i + 1), **sconfig)

        self.addLink(switches["s1"], switches["s2"], **gig_net)
        self.addLink(switches["s1"], switches["s4"], **megabit_net)
        self.addLink(switches["s2"], switches["s5"], **gig_net)
        self.addLink(switches["s2"], switches["s3"], **gig_net)
        self.addLink(switches["s3"], switches["s4"], **megabit_net)
        self.addLink(switches["s5"], switches["s4"], **gig_net)
       
        self.addLink(h1, switches["s1"], **host_link_config)
        self.addLink(h2, switches["s1"], **host_link_config)
        self.addLink(g1, switches["s1"], **host_link_config)

        self.addLink(h5, switches["s2"], **host_link_config)

        self.addLink(h3, switches["s3"], **host_link_config)
        self.addLink(h4, switches["s3"], **host_link_config)
        self.addLink(g2, switches["s3"], **host_link_config)

        self.addLink(ser1, switches["s4"], **host_link_config)

        self.addLink(ser2, switches["s5"], **host_link_config)



topos = {"networkslicingtopo": (lambda: NetworkSlicingTopo())}


try:
    if __name__ == "__main__":
        
        setLogLevel("info")

        topo = NetworkSlicingTopo()
        net = Containernet(
            topo=topo,
            switch=OVSKernelSwitch,
            build=False,
            autoSetMacs=True,
            autoStaticArp=True,
            link=TCLink
        )

        mgr = VNFManager(net)

        info("*** Connecting to the controller\n")
        controller = RemoteController("c1", ip="127.0.0.1", port=6633)
        net.addController(controller)

        info("\n*** Starting network\n")
        net.build()
        net.start()


except Exception as e: 
    print(e)
    net.stop()