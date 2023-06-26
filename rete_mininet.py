#!/usr/bin/env python3

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, RemoteController
from mininet.cli import CLI
from mininet.link import TCLink

class ComplexNetworkTopo(Topo):

    def __init__(self):

        Topo.__init__(self)

        # Create template host, switch, and link
        host_config = { "inNamespace":True }
        server_config = { "inNamespace":True }
        gig_net = { "bw": 1000 }
        megabit_net = { "bw": 100 }
        host_link = {}

        # Create switches
        for i in range(5):
            sconfig = {"dpid": "%016x" % (i + 1)}
            self.addSwitch("s%d" % (i + 1), **sconfig)

        # inter-switches networks

        self.addLink("s1", "s2", **gig_net)
        self.addLink("s2", "s3", **gig_net)

        self.addLink("s1", "s4", **megabit_net)
        self.addLink("s3", "s4", **megabit_net)

        self.addLink("s5", "s2", **gig_net)
        self.addLink("s5", "s4", **gig_net)

        # work-hosts configuration and links
        for i in range(4):
            self.addHost(f"h{i + 1}", **host_config)

        self.addLink("h1", "s1", **host_link)
        self.addLink("h2", "s1", **host_link)
        self.addLink("h3", "s3", **host_link)
        self.addLink("h4", "s3", **host_link)

        # gaming-only-hosts configuration and links
        for i in range(2):
            self.addHost(f"g{i + 1}", **host_config)

        self.addLink("g1", "s1", **host_link)
        self.addLink("g2", "s3", **host_link)

        # Servers configuration and links
        self.addHost("ps", **server_config)
        self.addLink("ps", "s5", **host_link)

        self.addHost("gs", **server_config)
        self.addLink("gs", "s4", **host_link)

topos = {"networkslicingtopo": (lambda: ComplexNetworkTopo())}

if __name__ == "__main__":
    topo = ComplexNetworkTopo()
    net = Mininet(
        topo=topo,
        switch=OVSKernelSwitch,
        build=False,
        autoSetMacs=True,
        autoStaticArp=True,
        link=TCLink,
    )
    controller = RemoteController("c1", ip="127.0.0.1", port=6633)
    net.addController(controller)
    net.build()
    net.start()
    CLI(net)
    net.stop()
