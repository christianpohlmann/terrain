#
# Copyright (C) 2014-2016 Christian Pohlmann
#
# Licensed under The MIT License (see LICENSE.md)
#
import numpy as np
import operator as o

class GenerationStrategy(object):
    '''This is the base class for all implemented height map generation schemes. It
    provides common functionality needed to post-process the raw height data generated
    by subclasses.
    '''

    def __init__(self, width, height, config):
        '''Constructor: Set attributes.'''
        self.width = width
        self.height = height
        self.config = config
        if 'seed' in config:
            np.random.seed(config['seed'])


    def _generate_raw(self):
        '''Initializes the heightmap with zeros. This method should be overriden in
        subclasses in order to perform a meaningful height map generation.
        '''
        self.heightmap = np.zeros([self.width, self.height])
        return self


    def __normalize(self):
        '''Normalizes the tile values after generation such that for each value x holds:
        0 <= x <= 1. Not used anymore because it leads to much worse results than the
        percentile approach. However, if normalization is preferred, just call this method
        instead of __calc_percentiles in method generate()
        '''
        mx = np.max(self.heightmap)
        # the (highly) unlikely case where mx=0 must be handled properly
        if mx == 0:
            self.heightmap = np.ones(self.heightmap.shape)
        else:
            for (i,j), x in np.ndenumerate(self.heightmap):
                self.heightmap[i][j] = x / mx
        return self


    def __calc_percentiles(self):
        '''Converts each value in the heightmap to the largest percentile in which it
        still lies. If values are the same, they are assigned the same percentile.
        '''
        arr_as_srtd_lst = sorted(list(np.ndenumerate(self.heightmap)),
                                 key = lambda x: x[1])
        percentiles_arr = np.zeros(self.heightmap.shape)
        last_percentile = None
        last_value = None
        for (k, ((i,j),v)) in enumerate(arr_as_srtd_lst):
            curr_percentile = (k+1.0)/len(arr_as_srtd_lst)
            if v == last_value:
                curr_percentile = last_percentile
            self.heightmap[i][j] = curr_percentile
            last_percentile = curr_percentile
            last_value = v
        return self


    def __calc_groups(self):
        '''Maps normalized tile values to groups. A group is a number indicating between
        which thresholds a value lies. The groups can later easily be mapped to
        color maps by a visualization strategy.
        '''
        thresholds = self.config['thresholds']
        if thresholds is None:
            raise Exception("The config parameter 'thresholds' must be set.")
        for ((i,j), x) in np.ndenumerate(self.heightmap):
            groupFound = False
            for k,t in enumerate(thresholds):
                if x < t:
                    self.heightmap[i][j] = k
                    groupFound = True
                    break
            if not groupFound:
                # assign to last group
                self.heightmap[i][j] = len(thresholds)
        return self


    def __get_neighbors(self, pt, shape):
        '''Get all neighbours for the given point pt. This function is used by the
        erosion filter. At most 8 neighbors are returned. The second parameter
        denotes the shape of the heightmap (i.e. width and height).
        '''
        x,y = pt
        w,h = shape
        neighbors = [((x-1,y),1),((x-1,y-1),1),((x-1,y+1),1),
                      ((x,y),2),((x,y-1),1),((x,y+1),1),
                      ((x+1,y),1),((x+1,y-1),1),((x+1,y+1),1)]
        return [((a,b),wt) for ((a,b),wt) in neighbors if a >= 0 and a < w and b >= 0 and b < h]


    def __smooth(self):
        '''Erosion filter. This filter reduces some of the noise from the generated data.
        After applying it, it is unlikely for tiles of high and low height to be
        adjacent.
        '''
        hm_copy = self.heightmap
        if 'erosion' in self.config:
            for m in range(self.config['erosion']):
                # copy heightmap in order not to distort the filter
                hm_copy = np.copy(self.heightmap)
                for i in range(self.width):
                    for j in range(self.height):
                        neighbors = self.__get_neighbors((i,j),
                                                         (self.width, self.height))
                        vals = [self.heightmap[k][l]*w for ((k,l),w) in neighbors]
                        sum_weights = sum([w for ((k,l),w) in neighbors])
                        hm_copy[i][j] = round(sum(vals)/(sum_weights))
                self.heightmap = hm_copy

        return self


    def generate(self):
        '''Generates height data by calling generate_raw() which should be overridden by
        all subclasses. Afterwards, a normalization is performed and finally each
        normalized value is mapped to a group.
        '''
        return self._generate_raw().__calc_percentiles().__calc_groups().__smooth()


class RandomStrategy(GenerationStrategy):
    '''Simple height map generation strategy: Uses uniformly distributed random values
    for each tile.
    '''

    def _generate_raw(self):
        '''Creates height map of random values.
        '''
        self.heightmap = np.random.rand(self.width, self.height)
        return self


class LinearFaultStrategy(GenerationStrategy):
    '''Generates a random height map by using the "fault" algorithm. This algorithm
    iteratively creates random straights and increases the height for all
    points either below or above the straight. Which side is increased is also
    decided randomly.
    '''

    def _generate_raw(self):
        '''Creates height map using the linear fault algorithm. The number of iterations
        is required as configuration parameter.
        '''

        if 'iterations' not in self.config:
            s = "Config parameter 'iterations' missing for linear fault generator"
            raise Exception(s)
        n = self.config['iterations']
        hm = np.zeros([self.width, self.height])
        for k in range(n):
            s = self.__random_straight()
            comp = [o.lt, o.le, o.gt, o.ge][np.random.randint(0,4)]
            for i in range(self.width):
                y = self.__get_y(s,i)
                for j in range(self.height):
                    curr = hm[i][j]
                    if (comp(y,j)):
                        hm[i][j] = curr+1
        self.heightmap = hm
        return self


    def __get_y(self, s, x):
        '''Get the y value of the straight s for a given x value.
        '''
        return s[0]*x+s[1]


    # A straight is created by generating two random points. In the unlikely
    # case of both x-values being equal, the below modifier is added
    # (or subtracted) to the first x-value.
    __MODIFIER = 0.00000001


    def __random_straight(self):
        '''Calculates a random straight that lies within the heightmap. This straight
        is used by the linear fault algorithm.
        '''
        (x1, y1) = (np.random.random()*self.width, np.random.random()*self.height)
        (x2, y2) = (np.random.random()*self.width, np.random.random()*self.height)
        if (x1 == x2):
            if x1 + __MODIFIER > self.width:
                x1 -= __MODIFIER
            else:
                x1 += __MODIFIER
        a = (y1-y2)/(x1-x2)
        b = y1 - a*x1
        return (a,b)
