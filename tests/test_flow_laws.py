"""Experimental laws must preserve physical rates across unit conventions."""

from dataclasses import replace

import numpy as np
import pytest

from gdmate.rheology_models.flow_laws import (
    GLEASON_TULLIS_1995,
    RYBACKI_2006,
    ExperimentalFlowLaw,
    to_aspect,
)


def test_crustal_prefactors():
    quartz = to_aspect(GLEASON_TULLIS_1995)
    anorthite = to_aspect(RYBACKI_2006, water_fugacity_pa=1e6)
    assert quartz.law.A == pytest.approx(8.57e-28, rel=5e-4, abs=0)
    assert anorthite.law.A == pytest.approx(7.13e-18, rel=5e-4, abs=0)
    assert (quartz.law.n, quartz.law.E, quartz.law.V) == (4, 223000, 0)
    assert (anorthite.law.n, anorthite.law.E, anorthite.law.V) == (3, 345000, 0)
    assert to_aspect(RYBACKI_2006, water_fugacity_pa=10e6).law.A == pytest.approx(
        10 * anorthite.law.A, abs=0
    )


def test_uniaxial_rate_preserved():
    # Uniaxial differential stress q: tau_II=q/sqrt(3), edot_II=sqrt(3)/2*edot_axial.
    exp = GLEASON_TULLIS_1995
    q_mpa, temperature = 100, 1000
    axial_rate = (exp.A * q_mpa**exp.n
                  * np.exp(-exp.E / (8.31446261815324 * temperature)))
    invariant_rate = np.sqrt(3) / 2 * axial_rate
    viscosity = to_aspect(exp).law.viscosity(invariant_rate, temperature)
    assert 2 * viscosity * invariant_rate == pytest.approx(q_mpa * 1e6 / np.sqrt(3))


def test_grain_size_and_fugacity_unit_invariance():
    exp = replace(RYBACKI_2006, p=2)
    si = replace(exp, A=exp.A * 1e-6**(exp.n + exp.r + exp.p),
                 stress_unit='Pa', grain_size_unit='m', fugacity_unit='Pa')
    assert to_aspect(exp, water_fugacity_pa=3e6).law.A == pytest.approx(
        to_aspect(si, water_fugacity_pa=3e6).law.A, rel=1e-12, abs=0
    )


@pytest.mark.parametrize('convention,factor', [
    ('uniaxial', 3**2.5 / 2), ('engineering_shear', 0.5), ('second_invariant', 1),
])
def test_strain_rate_conventions(convention, factor):
    exp = replace(GLEASON_TULLIS_1995, strain_rate_convention=convention)
    result = to_aspect(exp)
    assert result.strain_rate_factor == pytest.approx(factor)
    assert result.law.A == pytest.approx(exp.A * result.unit_factor * factor, abs=0)


def test_vector_viscosity_and_grain_size():
    law = to_aspect(replace(GLEASON_TULLIS_1995, p=2)).law
    eta = law.viscosity([1e-15, 16e-15], 800, grain_size_m=1e-3)
    assert eta[1] / eta[0] == pytest.approx(16**(-3 / 4))
    assert law.viscosity(1e-15, 800, grain_size_m=4e-3) / eta[0] == pytest.approx(2)


def test_explicit_water_assumptions():
    with pytest.raises(ValueError, match='fugacity'):
        to_aspect(RYBACKI_2006)
    with pytest.raises(ValueError, match='explicit'):
        to_aspect(GLEASON_TULLIS_1995, water_fugacity_pa=1e6)


@pytest.mark.parametrize('kwargs', [
    {'A': 0}, {'n': 0}, {'E': float('nan')}, {'stress_unit': 'bar'},
    {'grain_size_unit': 'km'}, {'strain_rate_convention': 'shear'},
])
def test_invalid_experimental_records(kwargs):
    with pytest.raises(ValueError):
        ExperimentalFlowLaw(**({'name': 'test', 'reference': 'test', 'A': 1,
                                'n': 3, 'E': 0,
                                'stress_unit': 'MPa', 'grain_size_unit': 'um',
                                'fugacity_unit': 'MPa',
                                'strain_rate_convention': 'uniaxial'} | kwargs))


@pytest.mark.parametrize('value', [0, -1, float('nan'), float('inf')])
def test_invalid_conversion_conditions(value):
    with pytest.raises(ValueError):
        to_aspect(RYBACKI_2006, water_fugacity_pa=value)
    with pytest.raises(ValueError):
        to_aspect(GLEASON_TULLIS_1995).law.viscosity(value, 800)


@pytest.mark.parametrize('missing', [
    'stress_unit', 'grain_size_unit', 'fugacity_unit', 'strain_rate_convention',
])
def test_units_and_convention_must_be_explicit(missing):
    record = dict(
        name='test', reference='test', A=1, n=3, E=0,
        stress_unit='MPa', grain_size_unit='um', fugacity_unit='MPa',
        strain_rate_convention='uniaxial',
    )
    del record[missing]
    with pytest.raises(TypeError, match=missing):
        ExperimentalFlowLaw(**record)


@pytest.mark.parametrize('convention,rate_factor,viscosity_factor', [
    ('uniaxial', np.sqrt(3) / 2, 1 / 3),
    ('engineering_shear', 1 / 2, 1),
    ('second_invariant', 1, 1 / 2),
])
def test_experimental_viscosity_matches_aspect(
    convention, rate_factor, viscosity_factor,
):
    # Synthetic law includes nonzero activation volume and grain-size dependence.
    exp = replace(RYBACKI_2006, p=2, V=1e-5, strain_rate_convention=convention)
    rate = np.array([1e-15, 1e-14])
    temperature, pressure, grain, fugacity = 900, 1e9, 100, 3
    eta = exp.viscosity(rate, temperature, pressure,
                        grain_size=grain, water_fugacity=fugacity)
    aspect = to_aspect(exp, water_fugacity_pa=fugacity * 1e6).law
    expected = aspect.viscosity(rate * rate_factor, temperature, pressure,
                               grain_size_m=grain * 1e-6)
    np.testing.assert_allclose(eta * 1e6, expected)
    # Directly invert the experimental equation to recover its stress in MPa.
    stress = ((rate * grain**exp.p / (exp.A * fugacity**exp.r))
              * np.exp((exp.E + pressure * exp.V)
                       / (8.31446261815324 * temperature)))**(1 / exp.n)
    np.testing.assert_allclose(eta, viscosity_factor * stress / rate)


def test_experimental_viscosity_uses_record_units():
    exp = replace(RYBACKI_2006, p=2)
    si = replace(exp, A=exp.A * 1e-6**(exp.n + exp.r + exp.p),
                 stress_unit='Pa', grain_size_unit='m', fugacity_unit='Pa')
    eta = exp.viscosity(1e-15, 900, grain_size=100, water_fugacity=3)
    eta_si = si.viscosity(1e-15, 900, grain_size=100e-6, water_fugacity=3e6)
    assert eta * 1e6 == pytest.approx(eta_si)
    assert np.isfinite(GLEASON_TULLIS_1995.viscosity(1e-15, 900))


@pytest.mark.parametrize('kwargs,match', [
    ({}, 'fugacity'),
    ({'water_fugacity': 1}, 'grain_size'),
    ({'water_fugacity': 0, 'grain_size': 100}, 'water_fugacity'),
    ({'water_fugacity': 1, 'grain_size': -1}, 'grain_size'),
    ({'water_fugacity': 1, 'grain_size': 100, 'temperature': 0}, 'temperature'),
    ({'water_fugacity': 1, 'grain_size': 100, 'pressure': np.nan}, 'pressure'),
    ({'water_fugacity': 1, 'grain_size': 100, 'strain_rate': 0}, 'strain_rate'),
])
def test_experimental_viscosity_invalid_inputs(kwargs, match):
    inputs = dict(strain_rate=1e-15, temperature=900) | kwargs
    with pytest.raises(ValueError, match=match):
        replace(RYBACKI_2006, p=2).viscosity(**inputs)


def test_experimental_viscosity_rejects_unmodelled_water():
    with pytest.raises(ValueError, match='explicit'):
        GLEASON_TULLIS_1995.viscosity(1e-15, 900, water_fugacity=1)
