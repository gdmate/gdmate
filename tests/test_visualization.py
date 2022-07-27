"""
Tests for analysis.visualization module
"""
import numpy as np
import matplotlib.pyplot as plt
import pyvista as pv

from gdmate.visualization import pyvista_vis

# Create very small mesh of 9 cells with 16 points and assign each a value
mesh = pv.UniformGrid(dims=(4, 4, 1)).cast_to_unstructured_grid()
mesh['sample_field'] = np.arange(9)

def test_pv_plot_2d():
    """ Test pv_plot_2d function """
    
    # Create Matplotlib figure/axes
    fig,ax = plt.subplots(1)

    # Attempt to plot the mesh on the axes, colored by the sample field and with
    # bounds restricted to 0-2 on the x and y axes.
    ax = pyvista_vis.pv_plot_2d(mesh,'sample_field',bounds=[0,2,0,2],
                                       ax=ax)

    # Test that the figure contains 1 axes
    assert len(fig.get_axes()) == 1
    
    # Test that the axes contains 1 image
    assert len(ax.get_images()) == 1
    
    # Test that the axes x limits are correct
    assert ax.get_xlim() == (0,2)

    # Test that the axes y limits are correct
    assert ax.get_ylim() == (0,2)
    
