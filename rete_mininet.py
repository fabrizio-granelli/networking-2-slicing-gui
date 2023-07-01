#!/usr/bin/env python3

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, RemoteController
from mininet.cli import CLI
from mininet.link import TCLink

from mininet.log import setLogLevel

class ComplexNetworkTopo(Topo):

    def __init__(self):

        Topo.__init__(self)

        work_hosts_num = 5
        gaming_hosts_num = 2

        # Create template host, switch, and link
        host_config = { "inNamespace":True }
        server_config = { "inNamespace":True }
        gig_net = { "bw": 1000 }
        megabit_net = { "bw": 100 }
        host_link_config = {}

        # Create switches
        for i in range(5):
            sconfig = {"dpid": "%016x" % (i + 1)}
            self.addSwitch("s%d" % (i + 1), **sconfig)

        # inter-switches networks

        self.addLink("s1", "s2", 1, 1, **gig_net)
        self.addLink("s1", "s4", 2, 1, **megabit_net)
        self.addLink("s2", "s5", 2, 1, **gig_net)
        self.addLink("s2", "s3", 3, 1, **gig_net)
        self.addLink("s3", "s4", 2, 3, **megabit_net)
        self.addLink("s5", "s4", 2, 2, **gig_net)

        # work-hosts configuration and links
        for i in range(work_hosts_num):
            h_n = i+1
            self.addHost(
                f"h{h_n}", 
                ip=f"10.0.0.{h_n}/24",
                # no problem, h_n <= 7
                mac=f"00:00:00:00:00:0{h_n}",
                **host_config
            )

        self.addLink("h1", "s1", 1, 3, **host_link_config)
        self.addLink("h2", "s1", 1, 4, **host_link_config)
        self.addLink("h3", "s3", 1, 3, **host_link_config)
        self.addLink("h4", "s3", 1, 4, **host_link_config)

        self.addLink("h5", "s2", 1, 4, **host_link_config)

        # gaming-only-hosts configuration and links
        for i in range(gaming_hosts_num):
            h_n = work_hosts_num+i+1
            self.addHost(
                f"g{i+1}", 
                ip=f"10.0.0.{h_n}/24",
                # no problem, h_n <= 7
                mac=f"00:00:00:00:00:0{h_n}",
                **host_config
            )

        self.addLink("g1", "s1", 1, 5, **host_link_config)
        self.addLink("g2", "s3", 1, 5, **host_link_config)

        # Servers configuration and links
        self.addHost(
            "gs", 
            ip=f"10.0.0.{work_hosts_num+gaming_hosts_num+1}/24",
            mac=f"00:00:00:00:01:01",
            **server_config
        )
        self.addHost(
            "ps", 
            ip=f"10.0.0.{work_hosts_num+gaming_hosts_num+2}/24",
            mac=f"00:00:00:00:01:02",
            **server_config
        )

        self.addLink("gs", "s4", 1, 4, **host_link_config)
        self.addLink("ps", "s5", 1, 3, **host_link_config)

topos = {"networkslicingtopo": (lambda: ComplexNetworkTopo())}

if __name__ == "__main__":

    setLogLevel("info")

    topo = ComplexNetworkTopo()
    net = Mininet(
        topo=topo,
        switch=OVSKernelSwitch,
        build=False,
        # autoSetMacs=True,
        autoStaticArp=True,
        link=TCLink,
    )
    controller = RemoteController("c1", ip="127.0.0.1", port=6633)
    net.addController(controller)
    net.build()
    net.start()
    CLI(net)
    net.stop()
