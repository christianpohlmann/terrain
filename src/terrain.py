from generation import RandomStrategy, LinearFaultStrategy
from visualization import RectangleStrategy, HexagonStrategy
import json
import sys


def register_gen_strategies():
    """Register generation strategies as key value pairs. The keys given
    here can then be referenced in the JSON scenario configuration.
    """
    strategies = {'random': RandomStrategy, 'linear-fault': LinearFaultStrategy}
    return strategies


def register_vis_strategies():
    """Register visualization strategies as key value pairs. The keys given
    here can then be referenced in the JSON scenario configuration.
    """
    strategies = {'rect': RectangleStrategy, 'hex': HexagonStrategy}
    return strategies


if __name__ == '__main__':
    gen_strategies = register_gen_strategies()
    vis_strategies = register_vis_strategies()

    if len(sys.argv) < 2:
        print('No configuration file given.')
    with open(sys.argv[1]) as f:
        config = json.load(f)
        if 'colors' in config['visualization']:
            colors = config['visualization']['colors']
            config['visualization']['colors'] = [(r, g, b) for [r, g, b] in colors]

    conf_gen = config['generation']
    strategy = gen_strategies[conf_gen['strategy']](conf_gen['width'],
                                                    conf_gen['height'], conf_gen)
    heightmap = strategy.generate().heightmap

    conf_vis = config['visualization']
    strategy = vis_strategies[conf_vis['strategy']](heightmap, conf_vis)
    strategy.visualize()
