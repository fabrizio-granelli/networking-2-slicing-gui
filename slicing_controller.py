from os import walk
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

from typing import List, Optional, Dict, Set
from slicing.work_emergency import get_work_emergency_forbidden, get_work_emergency_mac_mapping

from slicing.gaming_slice import get_gaming_forbidden, get_gaming_mac_mapping

from slicing.net_structure import Mode, all_macs
from slicing.work_slice import get_work_mac_mapping, get_work_forbidden


class Slicing(app_manager.RyuApp):
    # Tested OFP version
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(Slicing, self).__init__(*args, **kwargs)
        setLogLevel("info")


        #Bind host MAC adresses to interface
        self.mac_to_port: List[Optional[Dict[int, Dict[str, int]]]] = [ None, None, None ] 
        self.forbidden: List[Optional[Dict[str, Set[str]]]] = [ None, None, None ] 

        self.mac_to_port[Mode.WORK_MODE] = get_work_mac_mapping()
        self.forbidden[Mode.WORK_MODE] = get_work_forbidden()

        self.mac_to_port[Mode.GAMING_MODE] = get_gaming_mac_mapping()
        self.forbidden[Mode.GAMING_MODE] = get_gaming_forbidden()

        self.mac_to_port[Mode.WORK_EMERGENCY_MODE] = get_work_emergency_mac_mapping()
        self.forbidden[Mode.WORK_EMERGENCY_MODE] = get_work_emergency_forbidden()
        
        # The datapaths (of the switches) to send the delete command to 
        self.switch_datapaths = []

        # To set the initial mode
        self.current_mode = Mode.WORK_EMERGENCY_MODE

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Install the table-miss flow entry.
        match = parser.OFPMatch()
        actions = [
            parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)
        ]
        self.add_flow(datapath, 0, match, actions)

        # Save the datapath of the current switch
        self.switch_datapaths.append( datapath )

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

    def clear_flows( self ):

        for switch_dp in self.switch_datapaths:
            ofp_parser = switch_dp.ofproto_parser
            ofp = switch_dp.ofproto

            ofp_parser.OFPFlowMod(
                datapath=switch_dp,
                table_id=ofp.OFPTT_ALL,
                command=ofp.OFPFC_DELETE,
                out_port=ofp.OFPP_ANY,
                out_group=ofp.OFPG_ANY
            )

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # info(f"Ricevuto PACCHETTO")
        #Get packet info
        msg = ev.msg

        datapath = msg.datapath
        dpid = datapath.id
        # info(f"Ricevuto da {dpid}")

        ofproto = datapath.ofproto
        in_port = msg.match["in_port"]

        pkt = packet.Packet(msg.data)
        eth: Optional[ethernet.ethernet] = pkt.get_protocol(ethernet.ethernet) # type: ignore -> il metodo letteralmente filtra per tipo

        if (
            eth is None or
            eth.ethertype == ether_types.ETH_TYPE_LLDP
        ):
            # ignore lldp packet
            return

        dst_mac = eth.dst
        src_mac = eth.src

        if self.mac_to_port[self.current_mode] is None or self.forbidden[self.current_mode] is None:
            info("Network not already configured, packet dropped\n")
            return

        port_mapping: Dict[int, Dict[str, int]] = self.mac_to_port[self.current_mode] #type: ignore
        forbidden: Dict[str, Set[str]] = self.forbidden[self.current_mode] #type: ignore

        if src_mac in forbidden and dst_mac in forbidden[src_mac]:
            info("Forbidden ")
            info(f"[s] {src_mac} [d] {dst_mac} [SW] {dpid}\n")
            return 

        if dpid in port_mapping:
            if src_mac in all_macs() and dst_mac in all_macs():
                info(f"[s] {src_mac} [d] {dst_mac} [SW] {dpid}\n")

            if dst_mac in port_mapping[dpid]:
                # Found a predefined host in a predefined switch 


                out_port = port_mapping[dpid][dst_mac]
                actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
                match = datapath.ofproto_parser.OFPMatch(eth_src=src_mac, eth_dst=dst_mac)
                self.add_flow(datapath, 1, match, actions)
                self._send_package(msg, datapath, in_port, actions)

        elif dpid not in self.end_swtiches:
            # Found unknown switch, return
            out_port = ofproto.OFPP_FLOOD
            actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
            match = datapath.ofproto_parser.OFPMatch(in_port=in_port)
            self.add_flow(datapath, 1, match, actions)
            self._send_package(msg, datapath, in_port, actions)



