from .net_structure import all_macs, mac 

def get_work_emergency_mac_mapping():
    return {
        1: {
            # Direct connections
            mac("h1"): 3, mac("h2"): 4,

            # Fast connection
            mac("h3"): 2, mac("h4"): 2, mac("h5"): 2,
            mac("ps"): 2, 

            # TODO: Anche questa sarebbe corretta mac("ps"): 2, 
        },


        3: {
            # Direct connections
            mac("h3"): 3, mac("h4"): 4,

            # Fast connection
            mac("h1"): 2, mac("h2"): 2, mac("h5"): 2,
            mac("ps"): 2, 

            
        },

        4: {
            # Direct connections
            # mac("gs"): 4,

            # Fast work connections
            mac("h1"): 1, mac("h2"): 1,

            mac("h3"): 3, mac("h4"): 3, mac("h5"): 3,

            mac("ps"): 2


            # TODO: anche le connessioni laterali come fallback
        },

        5: {
            # Direct connections
            mac("ps"): 3,

            # fast connection
            mac("h1"): 2, mac("h2"): 2, mac("h3"): 2, mac("h4"): 2, mac("h5"): 2,
        },
    }


        # TODO: ma h5? sarebbe figo fare una linea a 100mb che passa per 4-5-2 per connettere
        # g1 e g2 a h5


def get_work_emergency_forbidden():
    # Isolating gaming hosts and server

    isolated_hosts = set([ mac("g1"), mac("g2"), mac("gs")])

    return {
        
        mac("g1"): set( all_macs() ),
        mac("g2"): set( all_macs() ),
        mac("gs"): set( all_macs() ),

        mac("h1"): isolated_hosts,
        mac("h2"): isolated_hosts,
        mac("h3"): isolated_hosts,
        mac("h4"): isolated_hosts,
        mac("h5"): isolated_hosts,
        # TODO: h5

        mac("ps"): isolated_hosts
    }