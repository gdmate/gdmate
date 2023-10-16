"""
Test for rheology.py
"""

import gdmate as gd
import numpy as np


def test_cond_geotherm():
    """ Test cond_geotherm function """

    # Most tests in this function involve creating small (and unrealistic)
    # geotherms and verifying that all the outputs of cond_geotherm match
    # manual calculations

    # Testing on a model with 3 layers of thickness 1 km with A = 0, depth = 3
    bd_temps, bd_heat_flows, z, cond_temps = \
        gd.rheology.cond_geotherm(thicknesses=[1, 1, 1], depth=3,
            radiogenic_heat=[0., 0., 0.], surface_t=273,
            heat_flow=0.05, thermal_conductivity=2.5)
    
    assert((bd_temps == [273., 293., 313., 333.]).all())
    assert((bd_heat_flows == [0.05, 0.05, 0.05, 0.05]).all())
    assert((z == [0, 1000, 2000, 3000]).all())
    assert((cond_temps == [273., 293., 313., 333.]).all())


    # Testing on a model with 3 layers of thickness 1 km with A = 0, depth = 5
    bd_temps, bd_heat_flows, z, cond_temps = \
        gd.rheology.cond_geotherm(thicknesses=[1, 1, 1], depth=5,
            radiogenic_heat=[0., 0., 0.], surface_t=273,
            heat_flow=0.05, thermal_conductivity=2.5)

    assert((bd_temps == [273., 293., 313., 333.]).all())
    assert((bd_heat_flows == [0.05, 0.05, 0.05, 0.05]).all())
    assert((z == [0, 1000, 2000, 3000, 4000, 5000]).all())
    assert((cond_temps == [273., 293., 313., 333., 333., 333.]).all())


    # Testing on a model with 3 layers of thickness 1 km
    # Depth is set to 5 km and each layer has radiogenic_heat set to 1e-5 W/m^3
    bd_temps, bd_heat_flows, z, cond_temps = \
        gd.rheology.cond_geotherm(thicknesses=[1, 1, 1], depth=5,
            radiogenic_heat=[1e-5, 1e-5, 1e-5], surface_t=273,
            heat_flow=0.05, thermal_conductivity=2.5)

    assert((bd_temps == [273., 291., 305., 315.]).all())
    assert((np.round(bd_heat_flows, 2) == [0.05, 0.04, 0.03, 0.02]).all())
    assert((z == [0, 1000, 2000, 3000, 4000, 5000]).all())
    assert((cond_temps == [273., 291., 305., 315., 315., 315.]).all())
    

    # Testing on a model with 3 layers of thickness 1 km with variable
    # radiogenic heat production and depth = 5
    bd_temps, bd_heat_flows, z, cond_temps = \
        gd.rheology.cond_geotherm(thicknesses=[1, 1, 1], depth=5,
            radiogenic_heat=[1e-5, 2e-5, 5e-6], surface_t=273,
            heat_flow=0.05, thermal_conductivity=2.5)
    
    assert((bd_temps == [273., 291., 303., 310.]).all())
    assert((np.round(bd_heat_flows, 3) == [0.05, 0.04, 0.02, 0.015]).all())
    assert((z == [0, 1000, 2000, 3000, 4000, 5000]).all())
    assert((cond_temps == [273., 291., 303., 310., 310., 310.]).all())

    # Testing on a model with 3 layers of thickness 1-3 km with variable
    # radiogenic heat production and depth = 8
    bd_temps, bd_heat_flows, z, cond_temps = \
        gd.rheology.cond_geotherm(thicknesses=[3, 1, 2], depth=8,
            radiogenic_heat=[1e-5, 5e-6, 5e-6], surface_t=273,
            heat_flow=0.05, thermal_conductivity=2.5)
    
    assert((bd_temps == [273., 315., 322., 330.]).all())
    assert((np.round(bd_heat_flows, 3) == [0.05, 0.02, 0.015, 0.005]).all())
    assert((z == [0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000]).all())
    assert((cond_temps == 
            [273., 291., 305., 315., 322., 327., 330., 330., 330.]).all())

    # Testing on a model with 1 lithospheric layer
    bd_temps, bd_heat_flows, z, cond_temps = \
        gd.rheology.cond_geotherm(thicknesses=[3], depth=5,
            radiogenic_heat=[1e-5], surface_t=273,
            heat_flow=0.05, thermal_conductivity=2.5)
    
    assert((bd_temps == [273., 315.]).all())
    assert((np.round(bd_heat_flows, 3) == [0.05, 0.02]).all())
    assert((z == [0, 1000, 2000, 3000, 4000, 5000]).all())
    assert((cond_temps == [273., 291., 305., 315., 315., 315.]).all())

    # Testing on a model with 2 lithospheric layers
    bd_temps, bd_heat_flows, z, cond_temps = \
        gd.rheology.cond_geotherm(thicknesses=[3, 1], depth=6,
            radiogenic_heat=[1e-5, 5e-6], surface_t=273,
            heat_flow=0.05, thermal_conductivity=2.5)
    
    assert((bd_temps == [273., 315., 322.]).all())
    assert((np.round(bd_heat_flows, 3) == [0.05, 0.02, 0.015]).all())
    assert((z == [0, 1000, 2000, 3000, 4000, 5000, 6000]).all())
    assert((cond_temps == 
            [273., 291., 305., 315., 322., 322., 322.]).all())


    # Testing on a model with 4 lithospheric layers
    bd_temps, bd_heat_flows, z, cond_temps = \
        gd.rheology.cond_geotherm(thicknesses=[3, 1, 2, 2], depth=9,
            radiogenic_heat=[1e-5, 5e-6, 5e-6, 1e-6], surface_t=273,
            heat_flow=0.05, thermal_conductivity=2.5)
    
    assert((bd_temps == [273., 315., 322., 330., 333.2]).all())
    assert((np.round(bd_heat_flows, 3) == 
            [0.05, 0.02, 0.015, 0.005, 0.003]).all())
    assert((z == 
            [0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000]).all())
    assert((cond_temps == 
            [273., 291., 305., 315., 322., 327., 330., 331.8, 333.2, 
             333.2]).all())

def test_adiab_geotherm():
    # Testing adiab_geotherm on a small scale with easy-to-handle numbers
    # These numbers have been chosen specifically so that the adiabatic
    # temperature doubles with every 1 km increase in depth.
    adiab_temps = gd.rheology.adiab_geotherm([0, 1000, 2000, 3000], ast=1573,
                                              gravity=10.0, 
                                              thermal_expansivity=0.01,
                                              heat_capacity=100, depth=3)
    assert((adiab_temps == [1573., 3146., 6292., 12584.]).all())

def test_geotherm():
    """ Test geotherm function """

    # Most tests in this function involve creating small (and unrealistic)
    # geotherms and verifying that all the outputs of geotherm match
    # manual calculations. Many of the test parameters are very similar to
    # those found in test_cond_geotherm, but because geotherm also considers
    # adiabatic heat transfer, it produces different results than cond_geotherm.
    
    # Testing on a model with 3 1 km layers with A = 0. Depth is set to 5 km.
    # Adiabatic surface temperature is set to 0 K, resulting in no adiabatic
    # geotherm.
    bd_temps, bd_heat_flows, z, combined_temps, cond_temps, adiab_temps = \
        gd.rheology.geotherm(thicknesses=[1, 1, 1], depth=5,
            radiogenic_heat=[0., 0., 0.], surface_t=273,
            heat_flow=0.05, thermal_conductivity=2.5, ast=0, gravity=10.0,
            thermal_expansivity=0.01, heat_capacity=100, plot=False, save=False)
    
    assert((bd_temps == [273., 293., 313., 333.]).all())
    assert((bd_heat_flows == [0.05, 0.05, 0.05, 0.05]).all())
    assert((z == [0, 1000, 2000, 3000, 4000, 5000]).all())
    assert((cond_temps == [273., 293., 313., 333., 333., 333.]).all())
    assert((adiab_temps == [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]).all())
    assert((combined_temps == cond_temps).all())


    # Testing on a model with 3 1 km layers with no radiogenic heat production
    # Adiabatic geotherm has been fixed to start at 1 K and double every 1 km
    bd_temps, bd_heat_flows, z, combined_temps, cond_temps, adiab_temps = \
        gd.rheology.geotherm(thicknesses=[1, 1, 1], depth=5,
            radiogenic_heat=[0., 0., 0.], surface_t=273,
            heat_flow=0.05, thermal_conductivity=2.5, ast=1, gravity=10.0,
            thermal_expansivity=0.01, heat_capacity=100, plot=False, save=False)

    assert((bd_temps == [273., 293., 313., 333.]).all())
    assert((bd_heat_flows == [0.05, 0.05, 0.05, 0.05]).all())
    assert((z == [0, 1000, 2000, 3000, 4000, 5000]).all())
    assert((cond_temps == [273., 293., 313., 333., 333., 333.]).all())
    assert((adiab_temps == [1., 2., 4., 8., 16., 32.]).all())
    assert((combined_temps == [273., 294., 316., 340., 348., 364.]).all())


    # Testing on a model with 3 layers of thickness 1 km with A = 1e-5 W/m^3
    # Adiabatic geotherm has been fixed to start at 1 K and double every 1 km
    bd_temps, bd_heat_flows, z, combined_temps, cond_temps, adiab_temps = \
        gd.rheology.geotherm(thicknesses=[1, 1, 1], depth=5,
            radiogenic_heat=[1e-5, 1e-5, 1e-5], surface_t=273,
            heat_flow=0.05, thermal_conductivity=2.5, ast=1, gravity=10.0,
            thermal_expansivity=0.01, heat_capacity=100, plot=False, save=False)

    assert((bd_temps == [273., 291., 305., 315.]).all())
    assert((np.round(bd_heat_flows, 2) == [0.05, 0.04, 0.03, 0.02]).all())
    assert((z == [0, 1000, 2000, 3000, 4000, 5000]).all())
    assert((cond_temps == [273., 291., 305., 315., 315., 315.]).all())
    assert((adiab_temps == [1., 2., 4., 8., 16., 32.]).all())
    assert((combined_temps == [273., 292., 308., 322., 330., 346.]).all())
    

    # Testing on a model with 3 layers of thickness 1 km with variable
    # radiogenic heat production
    # Adiabatic geotherm has been fixed to start at 1 K and double every 1 km
    bd_temps, bd_heat_flows, z, combined_temps, cond_temps, adiab_temps = \
        gd.rheology.geotherm(thicknesses=[1, 1, 1], depth=5,
            radiogenic_heat=[1e-5, 2e-5, 5e-6], surface_t=273,
            heat_flow=0.05, thermal_conductivity=2.5, ast=1, gravity=10.0,
            thermal_expansivity=0.01, heat_capacity=100, plot=False, save=False)
    
    assert((bd_temps == [273., 291., 303., 310.]).all())
    assert((np.round(bd_heat_flows, 3) == [0.05, 0.04, 0.02, 0.015]).all())
    assert((z == [0, 1000, 2000, 3000, 4000, 5000]).all())
    assert((cond_temps == [273., 291., 303., 310., 310., 310.]).all())
    assert((adiab_temps == [1., 2., 4., 8., 16., 32.]).all())
    assert((combined_temps == [273., 292., 306., 317., 325., 341.]).all())


    # Testing on a model with 3 layers of thickness 1-3 km with variable
    # radiogenic heat production
    # Adiabatic geotherm has been fixed to start at 1 K and double every 1 km
    bd_temps, bd_heat_flows, z, combined_temps, cond_temps, adiab_temps = \
        gd.rheology.geotherm(thicknesses=[3, 1, 2], depth=8,
            radiogenic_heat=[1e-5, 5e-6, 5e-6], surface_t=273,
            heat_flow=0.05, thermal_conductivity=2.5, ast=1, gravity=10.0,
            thermal_expansivity=0.01, heat_capacity=100, plot=False, save=False)
    
    assert((bd_temps == [273., 315., 322., 330.]).all())
    assert((np.round(bd_heat_flows, 3) == [0.05, 0.02, 0.015, 0.005]).all())
    assert((z == [0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000]).all())
    assert((cond_temps == 
            [273., 291., 305., 315., 322., 327., 330., 330., 330.]).all())
    assert((adiab_temps == [1., 2., 4., 8., 16., 32., 64., 128., 256.]).all())
    assert((combined_temps == 
            [273., 292., 308., 322., 337., 358., 393., 457., 585.]).all())

            
    # Testing on a model with 1 layer of thickness 3 km
    # Adiabatic geotherm has been fixed to start at 1 K and double every 1 km
    bd_temps, bd_heat_flows, z, combined_temps, cond_temps, adiab_temps = \
        gd.rheology.geotherm(thicknesses=[3], depth=5,
            radiogenic_heat=[1e-5], surface_t=273,
            heat_flow=0.05, thermal_conductivity=2.5, ast=1, gravity=10.0,
            thermal_expansivity=0.01, heat_capacity=100, plot=False, save=False)
    
    assert((bd_temps == [273., 315.]).all())
    assert((np.round(bd_heat_flows, 3) == [0.05, 0.02]).all())
    assert((z == [0, 1000, 2000, 3000, 4000, 5000]).all())
    assert((cond_temps == [273., 291., 305., 315., 315., 315.]).all())
    assert((adiab_temps == [1., 2., 4., 8., 16., 32.]).all())
    assert((combined_temps == [273., 292., 308., 322., 330., 346.]).all())


    # Testing on a model with 2 layers of thickness 1-3 km with variable
    # radiogenic heat production
    # Adiabatic geotherm has been fixed to start at 1 K and double every 1 km
    bd_temps, bd_heat_flows, z, combined_temps, cond_temps, adiab_temps = \
        gd.rheology.geotherm(thicknesses=[3, 1], depth=6,
            radiogenic_heat=[1e-5, 5e-6], surface_t=273,
            heat_flow=0.05, thermal_conductivity=2.5, ast=1, gravity=10.0,
            thermal_expansivity=0.01, heat_capacity=100, plot=False, save=False)
    
    assert((bd_temps == [273., 315., 322.]).all())
    assert((np.round(bd_heat_flows, 3) == [0.05, 0.02, 0.015]).all())
    assert((z == [0, 1000, 2000, 3000, 4000, 5000, 6000]).all())
    assert((cond_temps == [273., 291., 305., 315., 322., 322., 322.]).all())
    assert((adiab_temps == [1., 2., 4., 8., 16., 32., 64.]).all())
    assert((combined_temps == [273., 292., 308., 322., 337., 353., 385.]).all())


    # Testing on a model with 4 layers of thickness 1-3 km with variable
    # radiogenic heat production
    # Adiabatic geotherm has been fixed to start at 1 K and double every 1 km
    bd_temps, bd_heat_flows, z, combined_temps, cond_temps, adiab_temps = \
        gd.rheology.geotherm(thicknesses=[3, 1, 2, 2], depth=9,
            radiogenic_heat=[1e-5, 5e-6, 5e-6, 1e-6], surface_t=273,
            heat_flow=0.05, thermal_conductivity=2.5, ast=1, gravity=10.0,
            thermal_expansivity=0.01, heat_capacity=100, plot=False, save=False)
    
    assert((bd_temps == [273., 315., 322., 330., 333.2]).all())
    assert((np.round(bd_heat_flows, 3) == 
            [0.05, 0.02, 0.015, 0.005, 0.003]).all())
    assert((z == 
            [0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000]).all())
    assert((cond_temps == 
            [273., 291., 305., 315., 322., 327., 330., 331.8, 333.2, 
             333.2]).all()) 
    assert((adiab_temps == 
            [1., 2., 4., 8., 16., 32., 64., 128., 256., 512.]).all())
    assert((combined_temps == 
            [273., 292., 308., 322., 337., 358., 393., 458.8, 588.2, 
             844.2]).all())
