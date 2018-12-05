"""This module contains functions to sweep parameter-space, creating MCNP
depletion inputs to calculate keff at EOL.
* AR
* core_z
* cool_r
* PD
* power
* enrich
"""
from pyDOE import lhs
import itertools
import os
import glob
import numpy as np
import tarfile

from mcnp_inputs import HomogeneousInput

# set seed for reproducibility
np.random.seed(1324291)

parameters = {'core_r'    : (10, 50, 30),         
              'fuel_frac' : (0.2, 0.95, 10),
              'ref_mult'  : (0.001, 0.15, 33),        
             }

dimensions = list(parameters.keys())
dims = len(parameters)
samples = 500

def gen_hypercube(samples, N):
    """Generate N-dimensional latin hypercube to sample dimensional reactor
    space.

    Arguments:
    ----------
        samples (int): number of test cases to try
        N (int): number of dimensions to test
    
    Returns:
    --------
        cube (ndarray): normalized, N-D latin hypercube
    """

    np.random.seed(4654562)
    hypercube = lhs(N, samples=samples)

    return hypercube

def grid_sampling():
    """Generate evenly-sampled grid space.
    """
    rangeset = []
    for dim in parameters.keys():
        bounds = parameters[dim]
        rangeset.append(np.linspace(bounds[0], bounds[1], bounds[2]))
    grid = list(itertools.product(*rangeset))
    
    array = np.zeros(len(grid), dtype={'names' : dimensions, 
                                       'formats' : ['f8']*dims})
    for idx, params in enumerate(grid):
        array[idx] = params

    return array

def fill_data_array(samples, parameters, cube):
    """Fill an ndarray with the sampling set generated by lhs.
    """
    # initialize array
    test_cases = np.zeros(samples, dtype={'names' : dimensions,
                                          'formats' : ['f8']*dims})
    # for all samples
    for sample_idx, sample in enumerate(cube):
        # get values for every dimension
        for dim_idx, dim in enumerate(sorted(dimensions)):
            l_limit = parameters[dim][0]
            u_limit = parameters[dim][1]
            # uniform distribution
            a = u_limit - l_limit
            b = l_limit
            # save to ndarray
            test_cases[sample_idx][dim] = b + cube[sample_idx][dim_idx] * a
    
    return test_cases

def write_inputs(sampling_data, config):
    """Write MCNP depletion inputs for sampled data.
    """
    datanames = sampling_data.dtype.names
    tarputs = tarfile.open('{0}_{1}_inps.tar'.format(config['fuel'],
                                                     config['cool']), 'w')
    for num, sample in enumerate(sampling_data):

        config['core_r'] = sample['core_r']
        config['fuel_frac'] = sample['fuel_frac']
        config['ref_mult'] = sample['ref_mult']

        input = HomogeneousInput(config=config)
        input.homog_core()
        
        # identifying header string for post-processing
        header_str = ''
        for param in sorted(parameters.keys()):
            header_str += str(round(sample[param], 5)) + ','
        # write the input and tar it
        filename = str(num) + '.i'
        input.write_input(filename, header_str)
        tarputs.add(filename)

    # write HTC input list
    htc_inputs = open('input_list.txt', 'w')
    htc_inputs.write('\n'.join(glob.glob("*.i")))
    htc_inputs.close()
        
    tarputs.add('input_list.txt')
    tarputs.close()

if __name__=='__main__':

    config = {'fuel' : 'UO2',
              'matr' : None,
              'cool' : 'CO2',
              'clad' : 'Inconel-718',
             }
    cube = gen_hypercube(samples, dims)
    data = grid_sampling()
    #data = fill_data_array(samples, parameters, cube)
    print(len(data))
    write_inputs(data, config)
    # cleanup
    os.system('rm *.i input_list.txt')
