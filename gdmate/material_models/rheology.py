import numpy as np

def cond_geotherm(thicknesses=[20,20,60],depth=600,
             radiogenic_heat=[1.e-6,2.5e-7,0.],surface_t=273,
             heat_flow=0.05296,thermal_conductivity=2.5):
    """
    Calculate conductive continental geotherm values
    after Chapman86 and Naliboff scripts. Designed to be combined with
    adiabatic geotherm (i.e., asthenosphere temperature set as LAB
    temperature).
    
    Parameters:
        thicknesses: Thicknesses of lithospheric units (km)
        depth: Depth of model (km)
        radiogenic_heat: Radiogenic heat production in each unit (W/m^3)
        surface_t: Surface temperature (K)
        heat_flow: Surface heat flow (W/m^3)
        thermal_conductivity: Thermal conductivity (W/m*K)
    
    Returns:
        temps: Conductive temperatures (K) at each layer boundary
        heat_flows: Heat flows (W/m^3) at each layer boundary
        z: Array of depths (m)
        tc: Conductive temperatures at each depth (K)
    """
    thick_m = [x*1000 for x in thicknesses]
    
    # Set up heat flows and temperatures list
    heat_flows = [heat_flow]
    temps = [surface_t]
    
    for x in range(len(thicknesses)):
    
        # Determine heat flows at each layer boundary
        heat_flows.append(heat_flows[x] - (radiogenic_heat[x]*thick_m[x]))
        
        # Determine temperatures at each layer boundary
        temps.append(
            temps[x] + (heat_flows[x]/thermal_conductivity)*thick_m[x] - 
            (radiogenic_heat[x]*thick_m[x]**2)/(2.*thermal_conductivity)
            )
        
    # Calculate geotherm
    z = np.arange(0,depth+1,1)*1000 # depths in m
    tc = np.zeros(depth+1) # empty array of temperature
    
    # Set boundary locations for slicing tc
    boundaries = [0,thicknesses[0],thicknesses[0]+thicknesses[1],
                  thicknesses[0]+thicknesses[1]+thicknesses[2],
                  depth+1]
    
    # Get each layer as separate depth array
    layers = []
    temp_layers = []
    for x in range(len(thicknesses)+1):
        layers.append(z[boundaries[x]:boundaries[x+1]])
        temp_layers.append(tc[boundaries[x]:boundaries[x+1]])

    # Assign appropriate temperature values to each set of depths
    for x in range(len(layers)-1):
        temp_layers[x] = (
            temps[x] + (heat_flows[x]/thermal_conductivity)*
            (layers[x]-boundaries[x]*1000) - 
            (radiogenic_heat[x]*((layers[x]-boundaries[x]*1000)**2))/
            (2*thermal_conductivity)
            )
    # Assign constant temperature to the asthenosphere before replacing with
    # adiabatic
    temp_layers[-1] = temp_layers[-1] + temps[-1]
    # Combine depths into single array
    tc = np.concatenate(temp_layers)

    
    return(temps,heat_flows,z,tc)

def adiab_geotherm(z,ast=1573,gravity=9.81,thermal_expansivity=2.e-5,
                   heat_capacity=750,depth=600):
    """
    Calculate adiabatic geotherm. Assumes numpy array of depths (z) has
    already been calculated using conc_geotherm()
    
    Parameters:
        z: Array of depths (m)
        ast: Adiabatic surface temperature (K)
        gravity: Gravitational acceleration (m/s^-2)
        thermal_expansivity: Thermal expansivity (K^-1)
        heat_capacity: Heat capacity (J/K*kg)
        depth: Depth of model (km)
    
    Returns:
        ta: Adiabatic temperature for each depth (K)
    """
    ta = np.zeros(depth+1) # empty array for ta
    for i in range(np.size(z)):
      if i==0:
        ta[i] = ast # By design, the adiabatic surface temperature is the LAB temp
      else:
        # See line 124 in source/adiabatic_conditions/compute_profile
        ta[i] = ta[i-1] * (
            1 + (thermal_expansivity * gravity * 1000 * 1./heat_capacity))
        
    return(ta)

def geotherm(thicknesses=[20,20,60],depth=600,
             radiogenic_heat=[1.e-6,2.5e-7,0.],surface_t=273,
             heat_flow=0.05296,thermal_conductivity=2.5,ast=1573,gravity=9.81,
             thermal_expansivity=2.e-5,heat_capacity=750,plot=True,
             save=True):
    """
    Calculate combined conductive and adiabatic geotherm, after Naliboff
    scripts.
    
    Parameters:
        thicknesses: Thicknesses of lithospheric units (km)
        depth: Depth of model (km)
        radiogenic_heat: Radiogenic heat production in each unit (W/m^3)
        surface_t: Surface temperature (K)
        heat_flow: Surface heat flow (W/m^3)
        thermal_conductivity: Thermal conductivity (W/m*K)
        ast: Adiabatic surface temperature (K)
        gravity: Gravitational acceleration (m/s^-2)
        thermal_expansivity: Thermal expansivity (K^-1)
        heat_capacity: Heat capacity (J/K*kg)
        plot: Whether to plot the geotherm
        save: Whether to save boundary temperatures and heat flows to
            separate csv file.
        
    Returns:
        temps: Conductive temperatures (K) at each layer boundary
        heat_flows: Heat flows (W/m^3) at each layer boundary
        z: Array of depths (m)
        tt: Temperature (K) of combined conductive and adiabatic geotherm at
            each depth.
        
    """
    # Conductive geotherm
    temps,heat_flows,z,tc = cond_geotherm(thicknesses=thicknesses,depth=depth,
                       radiogenic_heat=radiogenic_heat,surface_t=surface_t,
                       heat_flow=heat_flow,thermal_conductivity=
                       thermal_conductivity)
    
    # Adiabatic geotherm
    ta = adiab_geotherm(z=z,ast=ast,gravity=gravity,thermal_expansivity=
                        thermal_expansivity,heat_capacity=heat_capacity,
                        depth=depth)
    
    # Combined geotherm
    tt = tc + ta - ast
    
    print('Conductive Boundary Temperatures: ', temps)
    print('Conductive Boundary Heat Flows: ', heat_flows)
    
    print('LAB Depth       = ', sum(thicknesses), 'km')
    print('LAB Temperature = ', tt[sum(thicknesses)], 'K')
    print('Bottom Temperature = ',tt[-1], 'K')
    
    if plot==True:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.plot(tt,z/1000)
        ax.invert_yaxis()
        ax.set_xlabel('T (K)')
        ax.set_ylabel('Depth (km)')
    
    if save==True:
        output = pd.Series(data=np.concatenate((temps,heat_flows[0:-1],tt[-1]),axis=None),
                           index=['ts1','ts2','ts3','ts4','qs1','qs2','qs3','base'])
        
        lith = np.sum(thicknesses)
        
        filename = 'thermal_' + str(lith) + '_' + str(depth) + '.csv'
                                     
        output.to_csv(filename)
    
    return(temps,heat_flows,z,tt,tc,ta)