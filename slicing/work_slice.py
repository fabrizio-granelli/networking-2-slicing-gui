from .net_structure import mac 

def get_work_mac_mapping():
    return {
        1: {
            # Direct connections
            mac("h1"): 3, mac("h2"): 4, mac("g1"): 5,

            # Slow connection
            mac("gs"): 2, mac("g2"): 2,

            # Fast connection
            mac("h3"): 1, mac("h4"): 1, mac("h5"): 1,

            mac("ps"): 1,
        },

        2: {
            # Direct connections
            mac("h5"): 4,

            # Fast (lateral and server) connection
            mac("h1"): 1, mac("h2"): 1, mac("h3"): 3, mac("h4"): 3,

            mac("ps"): (2, 251),

            # Fast (bottom, slow bottleneck) connection
            mac("g1"): (2, 252), mac("g2"): (2, 252),   

            # Gaming server missing: no hosts need to contact that host
        },

        3: {
            # Direct connections
            mac("h3"): 3, mac("h4"): 4, mac("g2"): 5,

            # Slow connection
            mac("gs"): 2, mac("g1"): 2,

            # Fast connection
            mac("h1"): 1, mac("h2"): 1, mac("h5"): 1,

            mac("ps"): 1,
        },

        4: {
            # Direct connections
            mac("gs"): 4,

            # Slow gaming connections
            mac("g1"): 1,
            mac("g2"): 3,

            # No other connections in work mode
            # TODO: maybe h5?
            mac("h5"): (2,45),
        },

        5: {
            # Direct connections
            mac("ps"): 3,

            # fast connection  dst, {src : (output port, output queue)}
            mac("h1"): {mac("ps") : (1,521)}, mac("h2"): {mac("ps"):(1,521)}, mac("h3"): {mac("ps"):(1,521)}, mac("h4"): {mac("ps"):(1,521)}, mac("h5"): {mac("ps"):(1,521), mac("g1") : (1,522),mac("g2") : (1,522)},

            #
            mac("g1"): (2,54), mac("g2"): (2,54)


        },
    }



def get_work_forbidden():
    # For gaming hosts, forbidden communications to work hosts and production server
    gaming_host_forbidden = set([ mac("h1"), mac("h2"), mac("h3"), mac("h4"), mac("ps") ])

    # For work hosts, forbidden communications to gaming hosts and gaming server
    work_host_forbidden = set([ mac("g1"), mac("g2"), mac("gs") ])
    
    return {
        
        mac("g1"): gaming_host_forbidden,
        mac("g2"): gaming_host_forbidden,

        mac("h1"): work_host_forbidden,
        mac("h2"): work_host_forbidden,
        mac("h3"): work_host_forbidden,
        mac("h4"): work_host_forbidden,
        # TODO: h5

        mac("ps"): work_host_forbidden,
        mac("gs"): gaming_host_forbidden,

    }
