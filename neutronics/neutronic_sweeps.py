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
import os
import glob
import numpy as np
import tarfile

from mcnp_inputs import HomogeneousInput, build_pyne_matlib

_dimensions = ['AR', 'core_r', 'cool_r', 'PD', 'power', 'enrich']

# number of samples for each sampled dimension
nsamples = 100

dims = {'core_r'  : (20, 50),         
        'AR'      : (0.7, 1.3),
        'PD'      : (1.4, 1.6),        
        'enrich'  : (0.3, 0.9),
        'cool_r'  : 0.5,
        'power'   : 150
       }

def get_sampling_params():
    """Decide which parameters are constants and which are ranges to be sampled.
    
    Returns:
    --------
        sampled (list): list of keys for sampled parameters
        const (list): keys for constant parameters
        dim (float): length of sampled parameters for LHS sampling function.
    """
    const = list(filter(lambda x: type(dims[x]) != tuple, dims.keys()))
    sampled = [x for x in dims.keys() if x not in const]
    
    dim = len(sampled)

    return sampled, const, dim


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

def fill_data_array(swept, const, cube):
    """Fill an ndarray with the sampling set generated by lhs and bounded by the
    ranges provided for each sampled dimension.

    Arguments:
    ----------
        swept (list): keys for sampled dimensions
        const (list): keys for constant dimensions
        cube (ndarray): latin hypercube 

    Returns:
    --------
        rxt_confs (ndarray): array of data for every reactor configuration. This
        data is used to build MCNP6 input files.
    """
    # initialize array
    rxt_confs = np.zeros(nsamples, dtype={'names' : list(dims.keys()),
                                          'formats' : ['f8']*len(dims)})
    # for all samples in latin hypercube
    for sample_idx, sample in enumerate(cube):
        # set values for every sampled dimension
        for dim_idx, dim in enumerate(swept):
            # skip constants
            l_limit = dims[dim][0]
            u_limit = dims[dim][1]
            # uniform distribution
            a = u_limit - l_limit
            b = l_limit
            # save to ndarray
            rxt_confs[sample_idx][dim] = b + cube[sample_idx][dim_idx] * a
        # set constant value dimensions
        for dim in const:
            rxt_confs[sample_idx][dim] = dims[dim]
    
    return rxt_confs

def write_inputs(sampling_data):
    """Write MCNP depletion inputs for each reactor configuration.
    
    Arguments:
    ----------
        sampling_data (ndarray): array of reactor configurations, one for each
        MCNP6 input file.
    """
    # build PyNE material library
    pyne_mats = build_pyne_matlib()
    # initialize tarball to save input files
    tarputs = tarfile.open('smpl_mcnp_depl_inps.tar', 'w')
    # generate inputs
    for num, sample in enumerate(sampling_data):
        input = HomogeneousInput(sample['core_r'],
                                 sample['core_r']*sample['AR'],
                                 sample['power'], pyne_mats)
        homog_comp = input.homog_core(sample['enrich'],
                                      sample['cool_r'],
                                      sample['PD'])
        input.write_mat_string()
        
        # identifying header string for post-processing
        header_str = ''
        for param in _dimensions:
            header_str += str(round(sample[param], 5)) + ','
        # write the input and tar it
        filename = input.write_input(num, header_str)
        tarputs.add(filename)

    # write HTC input list
    htc_inputs = open('input_list.txt', 'w')
    htc_inputs.write('\n'.join(glob.glob("*.i")))
    htc_inputs.close()
        
    tarputs.add('input_list.txt')
    tarputs.close()

if __name__=='__main__':
    swept, const, dim = get_sampling_params()
    cube = gen_hypercube(nsamples, dim)
    data = fill_data_array(swept, const, cube)
    write_inputs(data)
    # cleanup
    os.system('rm *.i input_list.txt')
