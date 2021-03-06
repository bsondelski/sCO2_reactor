# Matplotlib imports
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import matplotlib.axis
from matplotlib import cm, rc
from matplotlib.ticker import LinearLocator, FormatStrFormatter, ScalarFormatter
import numpy as np
import math


def plot(results, key, titles):
    """Produce surface plot of the flow results as function of PD and coolant
    channel diameter.
    """
    # get parametric sweep data
    N = int(math.sqrt(len(results.data)))
    M = results.data[key].reshape(N, N)
    R = results.data['r'].reshape(N, N)
    PD = results.data['pd'].reshape(N, N)

    fig = plt.figure()
    ax = fig.gca(projection='3d')
    surf = ax.plot_surface(R, PD, M,
                           cmap=cm.viridis, linewidth=0,
                           vmin=0, vmax=np.nanmax(M),
                           antialiased=False)

    # set x/y axis labels, ticks
    ax.set_xlabel("Coolant Channel Diameter [m]", fontsize=7)
    plt.xticks(rotation=25, fontsize=6)
    ax.set_ylabel("Fuel Pitch to Coolant D Ratio [-]", fontsize=7)
    plt.yticks(rotation=25, fontsize=6)
    ax.set_zlabel(titles[key][1], fontsize=7)

    # Customize the z axis.
    ax.set_zlim(np.nanmin(M), np.nanmax(M))
    ax.zaxis.set_major_locator(LinearLocator(10))
    ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))

    # edit z tick labels
    for t in ax.zaxis.get_major_ticks():
        t.label.set_fontsize(6)
    niceMathTextForm = ScalarFormatter(useMathText=True)
    ax.w_zaxis.set_major_formatter(niceMathTextForm)
    ax.ticklabel_format(axis="z", style="sci", scilimits=(0, 0))
    plt.title(titles[key][0])

    # Add a color bar which maps values to colors.
    fig.colorbar(surf, shrink=0.5, aspect=5, format='%.0e')

    return plt
