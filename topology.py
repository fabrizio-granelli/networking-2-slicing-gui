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
    
class NetworkTopology(Topo):

    
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
            ip="10.0.0.3/24",
            mac="00:00:00:00:00:03",
            docker_args={"hostname": "h3"}
        )
        h4 = self.addHost(
            "h4",
            cls=DockerHost,
            dimage="dev_test",
            ip="10.0.0.4/24",
            mac="00:00:00:00:00:04",
            docker_args={"hostname": "h4"}
        )
        h5 = self.addHost(
            "h5",
            cls=DockerHost,
            dimage="dev_test",
            ip="10.0.0.5/24",
            mac="00:00:00:00:00:05",
            docker_args={"hostname": "h5"}
        )
        g1 = self.addHost(
            "g1",
            cls=DockerHost,
            dimage="dev_test",
            ip="10.0.0.6/24",
            mac="00:00:00:00:00:06",
            docker_args={"hostname": "g1"}
        )

        g2 = self.addHost(
            "g2",
            cls=DockerHost,
            dimage="dev_test",
            ip="10.0.0.7/24",
            mac="00:00:00:00:00:07",
            docker_args={"hostname": "g2"}
        )
        g_serv = self.addHost(
            "g_serv",
            cls=DockerHost,
            dimage="dev_test",
            ip="10.0.0.8/24",
            mac="00:00:00:00:01:01",
            docker_args={"hostname": "g_serv"}
        )
        p_serv = self.addHost(
            "p_serv",
            cls=DockerHost,
            dimage="dev_test",
            ip="10.0.0.9/24",
            mac="00:00:00:00:01:02",
            docker_args={"hostname": "p_serv"}
        )
        
        for i in range(5):
            sconfig = {"dpid": "%016x" % (i + 1)}
            self.addSwitch("s%d" % (i + 1), **sconfig)

        self.addLink("s1", "s2", 1, 1, **gig_net)
        self.addLink("s1", "s4", 2, 1, **megabit_net)
        self.addLink("s2", "s5", 2, 1, **gig_net)
        self.addLink("s2", "s3", 3, 1, **gig_net)
        self.addLink("s3", "s4", 2, 3, **megabit_net)
        self.addLink("s5", "s4", 2, 2, **gig_net)
       
        self.addLink("h1", "s1", 1, 3, **host_link_config)
        self.addLink("h2", "s1", 1, 4, **host_link_config)
        self.addLink("g1", "s1", 1, 5, **host_link_config)

        self.addLink("h5", "s2", 1, 4, **host_link_config)

        self.addLink("h3", "s3", 1, 3, **host_link_config)
        self.addLink("h4", "s3", 1, 4, **host_link_config)
        self.addLink("g2", "s3", 1, 5, **host_link_config)

        self.addLink("g_serv", "s4", 1, 4, **host_link_config)
        self.addLink("p_serv", "s5", 1, 3, **host_link_config)




#topos = {"networkslicingtopo": (lambda: NetworkTopology())}



try:
    if __name__ == "__main__":
        
        setLogLevel("info")

        topo = NetworkTopology()
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
        #net.addController("c0")

        info("\n*** Starting network\n")
        print("OK1")
      
        
        net.build()
        net.start()
        print("OK")
        print(check_output(["./queue_create.sh"]))
        
        k=CLI(net)

        net.stop()
except Exception as e: 
    print(e)
    # net.stop()
