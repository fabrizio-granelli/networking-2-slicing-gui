from collections import deque
from os import walk

from ryu.ofproto import ofproto_v1_3
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet, ipv4
from ryu.lib.packet import ether_types
from ryu.lib.packet import udp
from ryu.lib.packet import tcp
from ryu.lib.packet import icmp
from ryu.lib import hub
from mininet.log import info,debug, setLogLevel
import socket
import time
import subprocess
from subprocess import PIPE, STDOUT, check_output
import shlex
import argparse
import logging

from textwrap import wrap

from typing import List, Optional, Dict, Set, Tuple
from slicing.work_emergency import get_work_emergency_forbidden, get_work_emergency_mac_mapping

from slicing.gaming_slice import get_gaming_forbidden, get_gaming_mac_mapping

from slicing.net_structure import Mode, all_macs
from slicing.work_slice import get_work_mac_mapping, get_work_forbidden

from ryu.cfg import CONF
from ryu.lib.ovs.bridge import OVSBridge

OVSDB_ADDR = 'unix:/var/run/openvswitch/db.sock'

queues = {
    5: {
        1: [ 900, 100 ],
        2: [ 900, 100 ],
    },
    2: {
        2: [ 900, 100 ],
    },
    4: {
        2: [ 900, 100 ],
    },
}


class Slicing(app_manager.RyuApp):
    # Tested OFP version
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(Slicing, self).__init__(*args, **kwargs)
        setLogLevel("debug")

        logging.basicConfig(level=logging.INFO,
            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
            datefmt='%m-%d %H:%M')
        

        # To info logs even on the connected monitor
        # It is thread safe (by default)
        self.log_to_socket = deque()

        self.BIND_ADDRESS = "172.17.0.1"
        self.BIND_PORT = 9933

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
        self.switch_datapaths_cache = {}

        # To set the initial mode
        self.current_mode = Mode.WORK_MODE

        # To monitor incoming request to change the slicing
        self.thread = hub.spawn(self._monitor)


    def _info(self, msg: str):

        self.log_to_socket.appendleft(msg + "\n")
        logging.info(msg)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        dpid = datapath.id

        self._flow_entry_empty(datapath)

        # if dpid in queues:
        #     for port_id in queues[dpid]:
        #         for speed in queues[dpid][port_id]:
        #
        #             self._configure_queue(dpid, port_id, speed)

    def _flow_entry_empty(self, datapath):
        # Install the table-miss flow entry.
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch()
        actions = [
            parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)
        ]
        self.add_flow(datapath, 0, match, actions)

    # def _configure_queue(self, dpid:int, portid: int, max_rate: int):
    #
    #     info(f"Requested configuration of dpid: {dpid}, portid: {portid}, max_rate: {max_rate}")
    #     ovs_bridge = OVSBridge(CONF, datapath_id=dpid, ovsdb_addr=OVSDB_ADDR)
    #     info(ovs_bridge.set_qos(f"s{dpid}-eth{portid}",type='linux-htb',max_rate=str(max_rate)))

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.switch_datapaths_cache:
                debug('register datapath: %016x', datapath.id)
                self.switch_datapaths_cache[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.switch_datapaths_cache:
                debug('unregister datapath: %016x', datapath.id)
                del self.switch_datapaths_cache[datapath.id]

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        #Construct flow_mod message and send it.
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath, priority=priority, match=match, instructions=inst
        )
        datapath.send_msg(mod)

        logging.info(" ".join(["quarto", str(datapath.id), str(match)]));

    def _send_package(self, msg, datapath: app_manager.Datapath, in_port, actions):
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

    def _create_flow_queue(self, dpid: int, ip_src: str, ip_dst: str, queue_n: int, priority: int):
        command = [
            "ovs-ofctl",
            "add-flow",
            f"s{dpid}",
            f"ip,priority={priority},nw_src={ip_src},nw_dst={ip_dst},idle_timeout=0,actions=set_queue:{queue_n},normal"
        ]

        self._info("Running " + " ".join(command))

        completed = subprocess.run(command, stdout=PIPE, stderr=STDOUT)

        if completed.returncode == 0:
            self._info("Comando inviato")
            pass
        else:
            logging.info("ERROEEEEEEEE")
            info(completed.stdout)


    def init_flows_slice( self, slice ):

        assert slice == Mode.WORK_MODE or slice == Mode.GAMING_MODE or slice == Mode.WORK_EMERGENCY_MODE 

        self.current_mode = slice

        self._info("Slicing policy / mode changed")

        for dp_i in self.switch_datapaths_cache:

            switch_dp = self.switch_datapaths_cache[dp_i]

            ofp_parser = switch_dp.ofproto_parser
            ofp = switch_dp.ofproto

            mod = ofp_parser.OFPFlowMod(
                datapath=switch_dp,
                table_id=ofp.OFPTT_ALL,
                command=ofp.OFPFC_DELETE,
                out_port=ofp.OFPP_ANY,
                out_group=ofp.OFPG_ANY
            )

            switch_dp.send_msg(mod)
            
        self._info("Flows cleared")

        for dp_i in self.switch_datapaths_cache:
            switch_dp = self.switch_datapaths_cache[dp_i]

            self._flow_entry_empty(switch_dp)

        self._info("Initialized switches")


    

    def _monitor(self):

        debug("Thread started")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((self.BIND_ADDRESS, self.BIND_PORT))
            sock.listen()
            while True:
                # Infinite loop on a blocking accept call, in case the
                # socket get disconnected
                conn, addr = sock.accept()
                with conn:
                    logging.info(f"Connected by {addr}")
                    while True:
                        data = conn.recv(1024)
                        if not data:
                            break

                        msg_recv = data.decode("utf-8").split("_")
                        debug("\nRECV: ", msg_recv)

                        if msg_recv[0] == "SLICE":
                            self.init_flows_slice(int(msg_recv[1]))
                            conn.sendall("DONE".encode("UTF-8"))

                        elif msg_recv[0] == "PING":

                            sel = True

                            while sel is not None:
                                # Taking all the log lines in log_to_socket and sending them
                                # to the client to info them out
                                try:
                                    sel = self.log_to_socket.pop()
                                except IndexError:
                                    sel = None

                                if sel:
                                    # Splitting the text in finite-size chunks when sending
                                    # them to the client
                                    # TODO: padding?

                                    # Fine with ascii text
                                    chunks = [sel[i:i+1024] for i in range(0, len(sel), 1024)]

                                    logging.info(chunks)

                                    for chunk in chunks:
                                        conn.sendall(chunk.encode("UTF-8"))

                            conn.sendall("~~".encode("UTF-8"))

                        else:
                            debug("COMANDO SCONOSCIUTO")

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # info(f"Ricevuto PACCHETTO")
        #Get packet info
        msg = ev.msg

        datapath: app_manager.Datapath = msg.datapath
        dpid = datapath.id
        # info(f"Ricevuto da {dpid}")

        ofproto = datapath.ofproto
        in_port = msg.match["in_port"]

        pkt = packet.Packet(msg.data)
        # info(pkt)
        eth: Optional[ethernet.ethernet] = pkt.get_protocol(ethernet.ethernet) # type: ignore -> il metodo letteralmente filtra per tipo
        lv3_pkg: Optional[ipv4.ipv4] = pkt.get_protocol(ipv4.ipv4) # type: ignore

        if (
            eth is None or
            lv3_pkg is None or
            dpid is None or
            eth.ethertype == ether_types.ETH_TYPE_LLDP
        ):
            # ignore lldp packet
            return

        # dst_addr = eth.dst
        # src_addr = eth.src

        dst_addr = lv3_pkg.dst # type: ignore
        src_addr = lv3_pkg.src # type: ignore

        if self.mac_to_port[self.current_mode] is None or self.forbidden[self.current_mode] is None:
            # self._info("Network not already configured, packet dropped\n")
            return

        port_mapping: Dict[int, Dict[str, int]] = self.mac_to_port[self.current_mode] #type: ignore
        forbidden: Dict[str, Set[str]] = self.forbidden[self.current_mode] #type: ignore

        if src_addr in forbidden and dst_addr in forbidden[src_addr]:
            # self._info("Forbidden ")
            # self._info(f"[s] {src_addr} [d] {dst_addr} [SW] {dpid}\n")
            return 

        if dpid in port_mapping:
            # Debug info
            if src_addr in all_macs() and dst_addr in all_macs():
                self._info(f"\n[s] {src_addr} [d] {dst_addr} [SW] {dpid}")

            # Calculate packet destination

            if dst_addr in port_mapping[dpid]:
                # Found a predefined host in a predefined switch 

                out_port: Dict | Tuple | int = port_mapping[dpid][dst_addr]

                # Check if the out_port mapping uses input address
                if isinstance(out_port, Dict):
                    if src_addr in out_port:
                        out_port = out_port[src_addr]
                    else: 
                        logging.info("Butto via")
                        return

                if isinstance(out_port, Tuple):

                    out_port, queue_id = out_port

                    # info("QUEUEUEUEUEEUEUEUE")

                    # Setto il nuovo flow
                    self._create_flow_queue(
                        dpid=dpid,
                        ip_src=src_addr, 
                        ip_dst=dst_addr,
                        queue_n=queue_id,
                        priority=2
                    )

                    # Invio il pacchetto attuale
                    # Questo viene fatto senza queue, di fatto il pacchetto viaggera alla
                    # massima velocita
                    actions = [
                        # datapath.ofproto_parser.OFPActionSetQueue(queue_id=queue_id),
                        datapath.ofproto_parser.OFPActionOutput(out_port)
                        # datapath.ofproto_parser.OFPActionOutput(datapath.ofproto_parser.OFPP_NORMAL, 0)
                    ]
                    self._send_package(msg, datapath, in_port, actions)

                else:
                    logging.info(f"Invio alla porta: {out_port}")
                    logging.info(f"SWITCH: {out_port}")

                    actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]

                    match = datapath.ofproto_parser.OFPMatch(eth_type=0x800, ipv4_src=src_addr, ipv4_dst=dst_addr)

                    self.add_flow(datapath, 2, match, actions)
                    self._send_package(msg, datapath, in_port, actions)

        elif dpid not in self.end_swtiches:
            # Found unknown switch, return
            out_port = ofproto.OFPP_FLOOD
            actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
            match = datapath.ofproto_parser.OFPMatch(in_port=in_port)
            self.add_flow(datapath, 1, match, actions)
            self._send_package(msg, datapath, in_port, actions)




