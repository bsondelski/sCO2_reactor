import sys
import os
import numpy as np
from scipy.optimize import minimize_scalar, curve_fit
from subprocess import call, DEVNULL
from mcnp_inputs import HomogeneousInput
import fit_data as fd
import parse_outputs as po

from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter

target_keff = 1.01
# critical radius range to sweep
domain = (5, 28.75)

g_to_kg = 0.001

def crit_radius(config, func):
    """Get critical radius = f(fuel_frac)
    """
    f = config['fuel_frac']
    m = config['ref_mult']
    interp_keff = lambda r: (func([r, f, m])[0] - target_keff)**2
    
    res = minimize_scalar(interp_keff, args=(), 
                          method='bounded', bounds=(10, 50))
    
    return res.x
    
def fuel_frac(coolant, fuel, clad, matr, func):
    """Determine the optimal reflector thickness for a given reactor
    configuration.
    """
    rhos = {'CO2' : 252.638e-3, 'H2O' : 141.236e-3}
    config = {'fuel' : fuel,
              'matr' : matr,
              'cool' : coolant,
              'clad' : clad,
              'rho_cool' : rhos[coolant],
             }
    resname = '{0}_{1}_results.txt'.format(coolant, fuel)
    results = open(resname, '+w')
    results.write('fuel_frac,crit_radius\n') 
    results.close()

    for frac in np.linspace(0.3, 0.95, 10):
        results = open(resname, 'a')
        config['fuel_frac'] = frac
        res = minimize_scalar(refl_mult_mass, args=(config, func), 
                              method='bounded', bounds=(0.01, 0.6))
        config['ref_mult'] = res.x
        # get critical radius
        r = crit_radius(config, func)
        results.write('{0:.2f},{1:.5f},{2:.5f}\n'.format(frac, r,
                                                         config['ref_mult']))
        results.close()

        refl_mult(config, func)
    

def refl_mult_mass(mult, config, func):
    """
    """
    config['ref_mult' ] = mult
    r = crit_radius(config, func)
    config['core_r'] = r
    input = HomogeneousInput(config=config)
    homog_comp = input.homog_core()
    tot_mass = input.core_mass + input.refl_mass + input.PV_mass
    
    return tot_mass

def refl_mult(config, func):
    """Determine the optimal reflector thickness for a given reactor
    configuration.
    """

    mults = np.linspace(0.001, 0.6, 100)
    data = {'mass' : [], 'r' : [], 'mult' : mults, 'keff' : []}
    refl_res = open('refl_results.txt', 'a')
    for mult in mults:
        config['ref_mult'] = mult
        # get critical radius
        r = crit_radius(config, func)
        # get the masses
        config['core_r'] = r
        input = HomogeneousInput(config=config)
        homog_comp = input.homog_core()
        tot_mass = input.core_mass + input.refl_mass + input.PV_mass
        data['mass'].append(tot_mass/ 1000)
        data['r'].append(r) 
    

    poly = np.polyfit(
     
    fitted = np.add(popt[0]*np.power(mults, 2), np.add(popt[1]*mults, popt[2]))

    fig = plt.figure()
    plt.scatter(mults, data['mass'], c=data['r'], s=6,
                cmap=plt.cm.get_cmap('plasma', len(set(data['r']))))
    
    for m in func.grid[2]:
        if m > 0.6:
            break
        plt.axvline(x=m)
    
#    plt.plot(mults, fitted)
    plt.title('Fuel Frac: {0}'.format(config['fuel_frac']))
    plt.xlabel('reflector mult [-]')
    plt.ylabel('reactor mass [kg]')
    plt.savefig('{0}.png'.format(config['fuel_frac']))
    
    return mults[data['mass'].index(min(data['mass']))]

def test_interp(data, fn):
    
    from matplotlib import cm

    radii = np.linspace(10, 50, 50)
    mults = np.linspace(0.001, 0.07, 50)
    
    RR = []
    MM = []
    keff = []
    for r in radii:
        for m in mults:
            RR.append(r)
            MM.append(m)
            keff.append(fn([r, 0.1, m])[0])

    fig = plt.figure()
    ax = fig.gca(projection='3d')
    
    # Plot the surface.
    ax.scatter(RR,MM,keff)
    # Customize the z axis.
    ax.zaxis.set_major_locator(LinearLocator(10))
    ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))
    plt.show()

if __name__ == '__main__':
    data = po.load_from_csv('./crit_results.csv')
    fn = po.interpolate_grid(data)
    fuel_frac('CO2', 'UO2', 'Inconel-718', None,fn)
    
    config = {'fuel' : 'UO2',
              'matr' : None,
              'cool' : 'CO2',
              'clad' : 'Inconel-718',
              'rho_cool' : 252.638e-3,
              'fuel_frac' : 0.75
             }
#    refl_mult(config, fn)
#    test_interp(data, fn)