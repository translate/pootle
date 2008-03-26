from Pootle import pootle

def setup_module(module):
    """initialize global variables in the module"""
    parser = pootle.PootleOptionParser()
    options, args = parser.parse_args(["--servertype=dummy"])
    module.server = parser.getserver(options)
    # shortcuts to make tests easier
    module.potree = module.server.potree

