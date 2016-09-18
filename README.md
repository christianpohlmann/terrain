# terrain

![Sample image](http://nconc.de/terrain/example1_small.png)

## About
_terrain_ is an easily extensible procedural content generation tool for creating and visualizing heightmaps written in Python.
Currently two generation and two visualization strategies are supported. The code is quite terse with fewer than 300 LOC (excluding comments and blank lines).
### Generation stratgies
* Linear fault algorithm: Iterative algorithm using straights to determine areas to elevate/to lower.
* Random algorithm: Generates a non-iterative random heightmap (can produce acceptable results if erosion is enabled).

### Visualization strategies
* Hexagons: Display each tile as hexagon. Gives a smoother appearance than using rectangles.
* Rectangles: Display each tile as rectangle.

The generation strategy creates a _n_ times _m_ heightmap where each tile is put into a tile-class.
The mapping to tile-classes is performed based on each tile's percentile (according to its height value).
This leads to much better results than using simple normalization which might fail to exhaust the whole spectrum of available tile-classes.

The visualization strategy then paints the image based on the tile-class membership.

_terrain_ was written with extensibility in mind. See [Extensibility](#extensibility) for details on how to extend terrain with your own generation and visualization algorithms.

## Requirements
* Python 3.x
* PIL
* numpy

## Installation
Just clone this repository and run: `python3 <config>` where `<config>` refers to a configuration file where generation parameters can be specified. See [Configuration](#configuration) for details
about available configuration options.

## Configuration
Configuration files are JSON files with a simple setup: On the first level there are two entries named `"generation"` and `"visualization"`. Their parameters are as follows:
### generation
* `"strategy"`: Currently either `"linear-fault"` or `"random"`.
* `"seed"`: The seed of the random number generator.
* `"iterations"`: How many iterations should be performed for the heightmap generation (ignored by the random generation strategy).
* `"thresholds"`: List of numbers between 0 and 1 which determine the boundaries for tile classes.
As mentioned above, these boundaries are not relative height data, but represent percentiles.
* `"width"`: Number of tiles in x-direction.
* `"height"`: Number of tiles in  y-direction.
* `"erosion"`: Denotes how many erosion iterations should be applied.

### visualization
* `"strategy"`: Currently either `"hex"` or `"rect"`.
* `"filename"`: Output filename of generated image.
* `"sidelen_x"`: Width of each tile. Only used in the `"rect"` strategy.
* `"sidelen_y"`: Height of each tile. Only used in the `"rect"` strategy.
* `"edgelen"`: Length of a single edge of a hex tile. Only used in the `"hex"` strategy.
* `"colors"`: List of colors to paint tiles. Each color is a list of three numbers denoting a RGB triple. Note that each tile class needs to have exactly one color,
i.e. the length of the colors list must contain exactly one more element than the thresholds list.

Sample configuration files are contained in `examples/`.


## Extensibility
The code for both generation and both visualization strategies is well-documented enough to understand how to write new strategies. However, a brief
general documentation is given below.

### Adding a generation strategy
In order to add a new generation strategy is is enough to inherit from `GenerationStrategy` and override the method `_generate_raw`.
The actual heightmap data must be stored in `self.heightmap` which is a numpy array. Percentile mapping and erosion is handled in
the base class. After implementing a new generation strategy it must be registered in `terrain.py` inside the function `register_gen_strategies()` like this:

```
strategies['new_gen_strategy'] = NewGenStrategy
```

The strategy can now be referenced in JSON configuration files as `"new_gen_strategy"`.

### Adding a visualization strategy
Analogously to adding new generation strategies, if a new visualization strategy is desired, class `VisualizationStrategy`
must be inherited and method `_visualize()` must be overriden. An `ImageDraw` object is provided named `self.draw`.
Subsequently, the new visualization strategy must be registered in `terrain.py` inside the function `register_vis_strategies()` like this:

```
strategies['new_vis_strategy'] = NewVisStrategy
```

The strategy can now be referenced in JSON configuration files as `"new_vis_strategy"`.
