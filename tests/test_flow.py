"""
Tests for inputs.flow module
"""
from pytest import approx
from gdmate.inputs import flow

def test_get_published():
    """Test get_published function"""

    ol_dry_dis_hirth = flow.get_published(
        'olivine','hirth','dislocation','dry')
    
    assert ol_dry_dis_hirth == (1.1e5,3.5,0,0,530,18)

    ol_wet_dis_hirth = flow.get_published(
        'olivine','hirth','dislocation','wet')

    assert ol_wet_dis_hirth == (90,3.5,0,1.2,480,11)

    ol_dry_dif_hirth = flow.get_published(
        'olivine','hirth','diffusion','dry')

    assert ol_dry_dif_hirth == (1.5e9,1,3,0,375,2)

    ol_wet_dif_hirth = flow.get_published(
        'olivine','hirth','diffusion','wet')

    assert ol_wet_dif_hirth == (1.0e6,1,3,1,335,4)

def test_convert2SI():
    """Test convert2SI function"""

    ol_dry_dis_hirth = flow.get_published(
        'olivine','hirth','dislocation','dry')
    
    converted = flow.convert2SI(ol_dry_dis_hirth,COH=1000)

    assert converted == (approx((1.1e-16,3.5,0,0,530e3,18e-6)),1000)
