from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import udp
from ryu.lib.packet import tcp
from ryu.lib.packet import icmp
from ryu.lib import hub
from mininet.log import info, setLogLevel
import socket
import time
import subprocess
from subprocess import check_output
import shlex
import argparse
import logging

from typing import Dict, Optional, List, Set

SwitchMacToPort = Dict[str, int]

class Host:
    # Can be 0:WORK or 1:GAMING
    tipo: int

    def __init__(self, t: int):
        self.tipo = t

class Switch:
    my_id: int

    slow_ports: Set[int]
    fast_ports: Set[int]

    state_mac_to_port: Dict[ int, SwitchMacToPort ]

    def __init__(self, t: int):
        self.tipo = t

class State:
    # mac_to_port: Dict[int, SwitchMacToPort]

    hosts: List[Host]

    switch: Dict[int, Switch]

    

class Slicing(app_manager.RyuApp):
    # Tested OFP version
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    state: State

    def __init__(self, *args, **kwargs):
        super(Slicing, self).__init__(*args, **kwargs)
        setLogLevel("info")

        #Bind host MAC adresses to interface
        self.state = State();
        self.state.mac_to_port = {
            1: { "00:00:00:00:00:01": 3, "00:00:00:00:00:02": 4, "00:00:00:00:00:06": 5},
            2: { "00:00:00:00:00:05": 4 },
            3: { "00:00:00:00:00:03": 3, "00:00:00:00:00:04": 4, "00:00:00:00:00:07": 5},
            4: { "00:00:00:00:01:01": 4 },
            5: { "00:00:00:00:01:02": 3 },
        }


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        #Install the table-miss flow entry.
        match = parser.OFPMatch()
        actions = [
            parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)
        ]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        #Construct flow_mod message and send it.
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath, priority=priority, match=match, instructions=inst
        )
        datapath.send_msg(mod)

    def _send_package(self, msg, datapath, in_port, actions):
        data = None
        ofproto = datapath.ofproto
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=data,
        )
        datapath.send_msg(out)

    def _work_cofiguration(self):
        raise NotImplementedError();

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):

        #Get packet info
        msg = ev.msg

        datapath = msg.datapath
        dpid = datapath.id

        ofproto = datapath.ofproto
        in_port = msg.match["in_port"]

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return

        dst_mac = eth.dst
        src_mac = eth.src


        if dpid in self.state.mac_to_port:

            # Auto-learning source ports for inter-network ( inter-switch really )
            # communication
            if src_mac not in self.state.mac_to_port[dpid]:
                info(f"Saved {src_mac} from port {in_port} of switch {dpid}")
                # I save the port the packed was coming from
                self.state.mac_to_port[dpid][ src_mac ] = in_port

            # TODO: Check if a mac is reachable from the requesting host

            if dst_mac in self.state.mac_to_port[dpid]:

                info(f"Found a packet from {src_mac} to {dst_mac} in s{dpid}\n");

                # TODO: bloccare le comunicazioni tra pc di lavoro e di
                # gioco se sulla stessa rete

                out_port = self.state.mac_to_port[dpid][dst_mac]
                actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
                match = datapath.ofproto_parser.OFPMatch(eth_dst=dst_mac)
                self.add_flow(datapath, 1, match, actions)
                self._send_package(msg, datapath, in_port, actions)

        elif dpid not in self.end_swtiches:
            # Found unknown switch, return
            out_port = ofproto.OFPP_FLOOD
            actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
            match = datapath.ofproto_parser.OFPMatch(in_port=in_port)
            self.add_flow(datapath, 1, match, actions)
            self._send_package(msg, datapath, in_port, actions)



