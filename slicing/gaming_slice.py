
from .net_structure import mac 

def get_gaming_mac_mapping():
    return {
        1: {
            # Direct connections
            mac("h1"): 3, mac("h2"): 4, mac("g1"): 5,

            # Fast connection
            mac("h3"): 1, mac("h4"): 1, mac("h5"): 1,

            # Fast connection even for gaming
            mac("gs"): 1, mac("g2"): 1
        },

        2: {
            # Direct connections
            mac("h5"): 4,

            # Fast connection
            mac("h1"): 1, mac("h2"): 1, mac("h3"): 3, mac("h4"): 3,

            # Fast connection for gaming
            mac("g1"): 1, mac("g2"): 3,
            mac("gs"): 2,

            # Production server missing: no hosts should contact that host
        },

        3: {
            # Direct connections
            mac("h3"): 3, mac("h4"): 4, mac("g2"): 5,

            # Fast connection
            mac("h1"): 1, mac("h2"): 1, mac("h5"): 1,

            # Fast connection for gaming
            mac("gs"): 1, mac("g1"): 1,
        },

        4: {
            # Direct connections
            mac("gs"): 4,

            # Fast gaming connections
            mac("g1"): 1, mac("g2"): 2,

            mac("h1"): 2, mac("h2"): 2, mac("h3"): 2, mac("h4"): 2, mac("h5"): 2,
        },

        5: {
            # No production server i gaming mode
            # mac("ps"): 3,

            # fast connection
            mac("h1"): 1, mac("h2"): 1, mac("h3"): 1, mac("h4"): 1, mac("h5"): 1,
            mac("g2"): 1, mac("g1"): 1,

            mac("gs"): 2
        },
    }


        # TODO: ma h5? sarebbe figo fare una linea a 100mb che passa per 4-5-2 per connettere
        # g1 e g2 a h5


def get_gaming_forbidden():
    # Basically every host can communicate with the others, with the exeption of the production
    # server, that is isolated
    return {
        
        mac("g1"): set([ mac("ps")]),
        mac("g2"): set([ mac("ps")]),

        mac("h1"): set([ mac("ps")]),
        mac("h2"): set([ mac("ps")]),
        mac("h3"): set([ mac("ps")]),
        mac("h4"): set([ mac("ps")]),
        mac("h5"): set([ mac("ps")]),
        # TODO: h5

        mac("ps"): set([ mac("h1"), mac("h2"), mac("h3"), mac("h4"), mac("h5"), mac("g1"), mac("g2"), mac("gs") ]),
        mac("gs"): set([ mac("ps")])

    }
