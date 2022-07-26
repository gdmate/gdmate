"""
Module for flow law calculations
"""
import numpy as np

def get_published(mineral,source,creep,dryness):
    """
    Get published values for flow law.
    """
    props = (mineral,source,creep,dryness)

    if props == ('olivine','hirth','dislocation','dry'):
        A = 1.1e5 # MPa^-n um^m_diff COH^-r
        n = 3.5
        m_diff = 0
        r = 0
        E = 530 # kJ/mol

        # V taken from Table 2 but is variable
        V = 18 # 10^-6 m^3/mol

    elif props == ('olivine','hirth','dislocation','wet'):
        # Used values for constant COH of 1000 H/10^6Si
        A = 90 # MPa^-n um^m_diff COH^-r
        n = 3.5
        m_diff = 0
        r = 1.2
        E = 480 # kJ/mol
        V = 11 # 10^-6 m^3/mol

    elif props == ('olivine','hirth','diffusion','dry'):
        A = 1.5e9 # MPa^-n um^m_diff COH^-r
        n = 1
        m_diff = 3
        r = 0
        E = 375 #kJ/mol

        # Lower end of a range from 2-10
        V = 2 # 10^-6 m^3/mol

    elif props == ('olivine','hirth','diffusion','wet'):
        # Used values for constant COH of 1000 H/10^6Si
        A = 1.0e6
        n = 1
        m_diff = 3
        r = 1
        E = 335 #kJ/mol
        V = 4 # 10^-6 m^3/mol
    
    return(A,n,m_diff,r,E,V)
        
def convert2SI(values,COH=1000):
    """
    Convert published flow law values to SI units.
    
    Assumes units follow Hirth03
    """

    A_pub = values[0]
    n = values[1]
    m_diff = values[2]
    r = values[3]
    E_pub = values[4]
    V_pub = values[5]

    A_SI = A_pub * 1e6**(-n-r) * 1e-6**(m_diff) # s^-1 Pa^-n m^m_diff COH^-r
    E_SI = E_pub * 1000 # J/mol
    V_SI = V_pub * 1e-6 # m^3/mol

    values_SI = (A_SI,n,m_diff,r,E_SI,V_SI)

    return(values_SI,COH)

def scaleA(A_SI,n):
    """
    Scale A from uniaxial experiments for ASPECT.

    Implemented in Danneburg et al., 2017
    """
    A_scaled = 2**(n-1) * 3**((n+1)/2) * A_SI

    return(A_scaled)

def get_flow_law_parameters(mineral,source,creep,dryness):

    values = get_published(mineral,source,creep,dryness)
    print('Published Values:')
    print('A - prefactor (MPa^-n um^m_diff COH^-r): ',values[0])
    print('n - stress exponent: ',values[1])
    print('m_diff - grain size exponent: ',values[2])
    print('r - fugacity exponent: ',values[3])
    print('E - activation energy (kJ/mol)',values[4])
    print('V - activation volume (10^-6 m^3/mol)',values[5])

    converted = convert2SI(values,COH=1000)
    print('Converted to SI Units:')
    print('A (Pa^-n m^m_diff COH^-r')


    A_scaled = (converted[0][0],converted[0][1])