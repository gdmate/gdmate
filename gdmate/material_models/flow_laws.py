"""
Module for flow law calculations
"""
import numpy as np

def get_published(material,source,creep,dryness):
    """
    Get published values for flow law.

    Parameters:
        material : str
            Name of rock/mineral being deformed
        source : str 
            First author of original source publication
        creep : str
            Dislocation or diffusion creep
        dryness : str
            Whether material is wet or dry

    Returns:
        A : float
            Prefactor (MPa^-n-r um^m_diff s^-1)
        n : float 
            Stress exponent. Always 1 for diffusion creep.
        m_diff : float
            Grain size exponent. Always 0 for dislocation creep.
        r : float
            Fugacity exponent. Always 0 for dry rheology.
        E : float
            Activation energy (kJ/mol)
        V : float
            Activation volume (10^-6 m^3/mol)
    """
    # Combine properties into a tuple
    props = (material,source,creep,dryness)

    # Get values depending on tuple supplied
    if props == ('olivine','hirth','dislocation','dry'):
        A = 1.1e5 # MPa^-n-r um^m_diff s^-1
        n = 3.5
        m_diff = 0
        r = 0
        E = 530 # kJ/mol

        # V taken from Table 2 but is variable
        V = 18 # 10^-6 m^3/mol

    elif props == ('olivine','hirth','dislocation','wet'):
        # Used values for constant COH of 1000 H/10^6Si
        A = 90 # MPa^-n-r um^m_diff s^-1
        n = 3.5
        m_diff = 0
        r = 1.2
        E = 480 # kJ/mol
        V = 11 # 10^-6 m^3/mol

    elif props == ('olivine','hirth','diffusion','dry'):
        A = 1.5e9 # MPa^-n-r um^m_diff s^-1
        n = 1
        m_diff = 3
        r = 0
        E = 375 #kJ/mol

        # Lower end of a range from 2-10
        V = 2 # 10^-6 m^3/mol

    elif props == ('olivine','hirth','diffusion','wet'):
        # Used values for constant COH of 1000 H/10^6Si
        A = 1.0e6 # MPa^-n-r um^m_diff s^-1
        n = 1
        m_diff = 3
        r = 1
        E = 335 # kJ/mol
        V = 4 # 10^-6 m^3/mol

    elif props == ('quartzite','gleason','dislocation','wet'):
        # Water fugacity not included in units so not used for conversion
        A = 1.1e-4 # MPa^-n s^-1 um^m_diff s^-1
        n = 4
        m_diff = 0
        r = 0 # Not considered
        E = 223 # kJ/mol
        V = 0 # 10^-6 m^3/mol
    
    elif props == ('anorthite','rybacki','dislocation','wet'):
        # A reported as log(A) so converted to A here
        A = 10**0.2 # MPa^-n-r um^m_diff s^-1
        n = 3
        m_diff = 0
        r = 1
        E = 345 # kJ/mol
        V = 38 # 10^-6 m^3/mol
    
    return(A,n,m_diff,r,E,V)
        
def convert2SI(values):
    """
    Convert published flow law values to SI units.
    
    Assumes units follow those in Hirth and Kohlstedt, 2003.
    Only changes A, E, and V.

    Parameters:
        values : tuple of floats
            Published values in the form (A,n,m_diff,r,E,V)
    
    Return:
        values_SI : tuple of floats 
            Published values with A,E, and V in SI units (A_SI,n,m_diff,r,E_SI,V_SI)
    """

    # Unpack tuple
    A_pub = values[0]
    n = values[1]
    m_diff = values[2]
    r = values[3]
    E_pub = values[4]
    V_pub = values[5]

    # Apply unit conversions
    A_SI = A_pub * 1e6**(-n-r) * 1e-6**(m_diff) # s^-1 Pa^-n-r m^m_diff
    E_SI = E_pub * 1000 # J/mol
    V_SI = V_pub * 1e-6 # m^3/mol

    # Repack tuple
    values_SI = (A_SI,n,m_diff,r,E_SI,V_SI)

    return(values_SI)

def scaleA(A_SI,n):
    """
    Scale A from uniaxial experiments for ASPECT.

    Appropriate for relating strain rate to viscosity for a uniaxial strain experiment.

    Parameters:
        A_SI : float
            Prefactor in SI units (MPa^-n-r um^m_diff s^-1)
        n : float
            stress exponent
    
    Returns:
        A_scaled : float
            Scaled A in SI units (MPa^-n-r um^m_diff s^-1)
    """
    A_scaled = 3**((n+1)/2)/2 * A_SI

    return(A_scaled)

def get_flow_law_parameters(material,source,creep,dryness):
    """
    Get flow law parameters in correct units and scaled for ASPECT.

    Converts published values to SI units and then scales the prefactor (A).
    Prints the values at each step and returns the final values for use in 
    ASPECT.

    Parameters:
        material : str
            Name of rock/mineral being deformed
        source : str 
            First author of original source publication
        creep : str
            Dislocation or diffusion creep
        dryness : str
            Whether material is wet or dry

    Returns:
        A_scaled : float
            Scaled A in SI units (MPa^-n-r um^m_diff s^-1)
        n : float 
            Stress exponent. Always 1 for diffusion creep.
        m_diff : float
            Grain size exponent. Always 0 for dislocation creep.
        r : float
            Fugacity exponent. Always 0 for dry rheology.
        E_SI : float
            Activation energy in SI units (J/mol)
        V_SI : float
            Activation volume in SI units (m^3/mol)
    """

    # Get the published values
    values = get_published(material,source,creep,dryness)

    # Format to 2 decimal places and print.
    values_str = ['{:0.2e}'.format(x) for x in values]

    print('Published Values:')
    print('A - prefactor (MPa^-n-r um^m_diff s^-1): ',values_str[0])
    print('n - stress exponent: ',values_str[1])
    print('m_diff - grain size exponent: ',values_str[2])
    print('r - fugacity exponent: ',values_str[3])
    print('E - activation energy (kJ/mol)',values_str[4])
    print('V - activation volume (10^-6 m^3/mol)',values_str[5])

    # Convert values to SI units
    converted = convert2SI(values)

    # Format to 2 decimal places and print.
    converted_str = ['{:0.2e}'.format(x) for x in converted]

    print('\nConverted to SI Units:')
    print('A (Pa^-n-r m^m_diff s^-1): ',converted_str[0])
    print('E - activation energy (J/mol): ',converted_str[4])
    print('V - activation volume (m^3/mol): ',converted_str[5])

    # Scale the A prefactor
    A_scaled = scaleA(converted[0],converted[1])

    # Format to 2 decimal places and print.
    A_scaled_str = '{:0.2e}'.format(A_scaled)

    print('\nScaled A for ASPECT:')
    print('A scaled (Pa^-n-r m^m_diff s^-1): ',A_scaled_str)

    # Pull values from appropriate tuple for output.
    n = values[1]
    m = values[2]
    r = values[3]
    E_SI = converted[4]
    V_SI = converted[5]

    return(A_scaled,n,m,r,E_SI,V_SI)