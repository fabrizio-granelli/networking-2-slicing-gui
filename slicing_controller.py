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
from ryu.lib import hub
from mininet.log import info,debug, setLogLevel
import socket
import subprocess
from subprocess import PIPE, STDOUT, check_output
import logging

from typing import List, Optional, Dict, Set, Tuple
from slicing.work_emergency import get_work_emergency_forbidden, get_work_emergency_mac_mapping

from slicing.gaming_slice import get_gaming_forbidden, get_gaming_mac_mapping

from slicing.net_structure import Mode, all_macs, all_switches
from slicing.work_slice import get_work_mac_mapping, get_work_forbidden

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

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER) # type: ignore
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath

        self._flow_entry_empty(datapath)

    def _flow_entry_empty(self, datapath):
        # Install the table-miss flow entry.
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch()
        actions = [
            parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)
        ]
        self.add_flow(datapath, 0, match, actions)

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.switch_datapaths_cache:
                debug('register datapath: %016x', datapath.id)
                self.switch_datapaths_cache[datapath.id] = datapath

                if len(self.switch_datapaths_cache) == len(all_switches()):

                    command = [
                        "./queue_create.sh",
                    ]

                    self._info("Running " + " ".join(command))

                    completed = subprocess.run(command, stdout=PIPE, stderr=STDOUT)

                    if completed.returncode == 0:
                        self._info("Comando inviato")
                        pass
                    else:
                        logging.info("Errore invio comando " + " ".join(command))
                        info(completed.stdout)


        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.switch_datapaths_cache:
                debug('unregister datapath: %016x', datapath.id)
                del self.switch_datapaths_cache[datapath.id]

    def add_flow(self, datapath, priority, match, actions):
        '''
            Add flow to the flow table of the selected switch ( by its
            datapath )
        '''
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        #Construct flow_mod message and send it.
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath, priority=priority, match=match, instructions=inst
        )
        datapath.send_msg(mod)

    def _send_package(self, msg, datapath: app_manager.Datapath, in_port, actions):
        '''
            Sends a package directly using the controller, before the actual flow 
            table entry is used, so that the first ping 
        '''
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

    def _create_flow_queue(self, dpid: int, ip_src: str, ip_dst: str, queue_n: int, priority: int, port: int):
        '''
            To create flow table entry wrapping ovs-ofctl. Workaround to the
            ryu not fully-working queue implementation
        '''
        command = [
            "ovs-ofctl",
            "add-flow",
            f"s{dpid}",
            f"ip,priority={priority},nw_src={ip_src},nw_dst={ip_dst},idle_timeout=0,actions=set_queue:{queue_n},output={port},pop_queue"
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
        '''
            Method to re-initialize the switches to apply the slicing mode.
            Flow tables are cleared and the default route is configured
        '''

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
        '''
            Secondary thread that manages TCP connections from the GUI
        '''

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
        '''
            Main packet handling function. It works by using the predefined
            topology, based on the actual slice. 
        '''
        msg = ev.msg

        datapath: app_manager.Datapath = msg.datapath
        dpid = datapath.id

        ofproto = datapath.ofproto
        in_port = msg.match["in_port"]

        pkt = packet.Packet(msg.data)
        eth: Optional[ethernet.ethernet] = pkt.get_protocol(ethernet.ethernet) # type: ignore -> It literally filters by type
        lv3_pkg: Optional[ipv4.ipv4] = pkt.get_protocol(ipv4.ipv4) # type: ignore

        if (
            eth is None or
            lv3_pkg is None or
            dpid is None or
            eth.ethertype == ether_types.ETH_TYPE_LLDP
        ):
            # ignore lldp packet
            return

        dst_addr = lv3_pkg.dst # type: ignore
        src_addr = lv3_pkg.src # type: ignore

        if self.mac_to_port[self.current_mode] is None or self.forbidden[self.current_mode] is None:
            self._info("Network not already configured, packet dropped\n")
            return

        port_mapping: Dict[int, Dict[str, int]] = self.mac_to_port[self.current_mode] #type: ignore
        forbidden: Dict[str, Set[str]] = self.forbidden[self.current_mode] #type: ignore

        if src_addr in forbidden and dst_addr in forbidden[src_addr]:
            self._info("Forbidden packet")
            self._info(f"[s] {src_addr} [d] {dst_addr} [SW] {dpid}")
            return 

        if dpid in port_mapping:
            # Calculate packet destination

            # Prints packet useful informations
            if src_addr in all_macs() and dst_addr in all_macs():
                self._info(f"[s] {src_addr} [d] {dst_addr} [SW] {dpid}")

            if dst_addr in port_mapping[dpid]:
                # Found a predefined host in a predefined switch 

                out_port: Dict | Tuple | int = port_mapping[dpid][dst_addr]

                # Check if the out_port mapping uses input address
                if isinstance(out_port, Dict):
                    if src_addr in out_port:
                        out_port = out_port[src_addr]
                    else: 
                        logging.info("Undefined route")
                        return

                if isinstance(out_port, Tuple):
                    out_port, queue_id = out_port

                    self._create_flow_queue(
                        dpid=dpid,
                        ip_src=src_addr, 
                        ip_dst=dst_addr,
                        queue_n=queue_id,
                        priority=2,
                        port=out_port #type: ignore
                    )

                    # Invio il pacchetto attuale
                    # The packet is sent through the switch without applying any
                    # QoS rule. This in fact DOES NOT limit the first packet sent
                    actions = [ datapath.ofproto_parser.OFPActionOutput(out_port) ]
                    self._send_package(msg, datapath, in_port, actions)

                else:
                    self._info(f"Output Port: {out_port}")

                    actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]

                    match = datapath.ofproto_parser.OFPMatch(eth_type=0x800, ipv4_src=src_addr, ipv4_dst=dst_addr)

                    self.add_flow(datapath, 2, match, actions)
                    self._send_package(msg, datapath, in_port, actions)

        else:
            # Found unknown switch, no packet output
            self._info("Error! Found unknown switch")




