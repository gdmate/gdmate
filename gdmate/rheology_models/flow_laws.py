"""Record experimental power laws and convert them to ASPECT's convention.

Experimental law: edot = A * stress**n * grain_size**(-p) * fugacity**r
* exp(-(E + P*V)/(R*T)). Stress, grain size and fugacity use the record's
units; E and V always use J/mol and m**3/mol. Water content is metadata,
not a substitute for fugacity. No water equation of state is assumed.
"""

from dataclasses import dataclass, field
from math import isfinite

import numpy as np

__all__ = [
    'ExperimentalFlowLaw', 'AspectFlowLaw', 'PrefactorConversion',
    'GLEASON_TULLIS_1995', 'RYBACKI_2006', 'to_aspect',
]

_PRESSURE_UNITS = {'Pa': 1.0, 'MPa': 1e6}
_LENGTH_UNITS = {'m': 1.0, 'um': 1e-6}
_RATE_CONVENTIONS = {'uniaxial', 'engineering_shear', 'second_invariant'}
_GAS_CONSTANT = 8.31446261815324


def _positive(name, value):
    if not isfinite(value) or value <= 0:
        raise ValueError(f'{name} must be finite and positive')


@dataclass(frozen=True)
class ExperimentalFlowLaw:
    """Published coefficients, units, measurement convention and provenance.

    ``uniaxial`` means axial strain rate versus differential stress;
    ``engineering_shear`` means gamma_dot versus shear stress;
    ``second_invariant`` means edot_II versus deviatoric stress invariant.
    These conventions cannot be interchanged without converting A.
    ``A`` has units stress**(-n) * length**p * fugacity**(-r) / s.
    All unit fields and the strain-rate convention are required keyword
    arguments, even when p or r is zero.
    ``notes`` records experimental water conditions and other assumptions.
    """

    name: str
    reference: str
    A: float
    n: float
    E: float
    V: float = 0.0
    p: float = 0.0
    r: float = 0.0
    stress_unit: str = field(kw_only=True)
    grain_size_unit: str = field(kw_only=True)
    fugacity_unit: str = field(kw_only=True)
    strain_rate_convention: str = field(kw_only=True)
    notes: str = ''

    def __post_init__(self):
        _positive('A', self.A)
        _positive('n', self.n)
        for name in ('E', 'V', 'p', 'r'):
            if not isfinite(getattr(self, name)):
                raise ValueError(f'{name} must be finite')
        for name, units in (
            ('stress_unit', _PRESSURE_UNITS),
            ('grain_size_unit', _LENGTH_UNITS),
            ('fugacity_unit', _PRESSURE_UNITS),
            ('strain_rate_convention', _RATE_CONVENTIONS),
        ):
            if getattr(self, name) not in units:
                raise ValueError(f'Unsupported {name}: {getattr(self, name)}')


    def viscosity(
        self, strain_rate, temperature, pressure=0.0, *,
        grain_size=None, water_fugacity=None,
    ):
        """Return constitutive viscosity in the record's stress unit times s.

        Inputs broadcast as NumPy arrays. Strain rate is in s**(-1), using
        the record's experimental convention. Grain size and water fugacity
        must use ``grain_size_unit`` and ``fugacity_unit`` respectively.
        Pressure is always Pa and temperature always K, since E and V are SI.
        Supply grain size when p != 0 and water fugacity when r != 0.
        A law with r=0 does not accept a water fugacity adjustment.

        The experimental stress is obtained by inverting the recorded power
        law. Constitutive viscosity is stress/(3*axial_rate) for uniaxial
        data, stress/gamma_dot for engineering shear, and stress/(2*edot_II)
        for invariant data. Thus the result is physically comparable to
        ASPECT viscosity after converting its stress units and rate input.
        For a record with stress_unit='MPa', multiply the result by 1e6 to
        obtain Pa s. No plasticity or viscosity limits are applied.
        """
        if self.r != 0 and water_fugacity is None:
            raise ValueError(
                'An explicit water fugacity in experimental units is required'
            )
        if self.r == 0 and water_fugacity is not None:
            raise ValueError('This law has no explicit water fugacity dependence')
        if self.p != 0 and grain_size is None:
            raise ValueError('grain_size in experimental units is required')
        rate, temp, pres, grain, fugacity = np.broadcast_arrays(
            *[np.asarray(x, dtype=float) for x in (
                strain_rate, temperature, pressure,
                1.0 if grain_size is None else grain_size,
                1.0 if water_fugacity is None else water_fugacity,
            )]
        )
        for name, values in (
            ('strain_rate', rate), ('temperature', temp),
            ('grain_size', grain), ('water_fugacity', fugacity),
        ):
            if not np.all(np.isfinite(values) & (values > 0)):
                raise ValueError(f'{name} must be finite and positive')
        if not np.all(np.isfinite(pres)):
            raise ValueError('pressure must be finite')
        factor = {
            'uniaxial': 1 / 3,
            'engineering_shear': 1.0,
            'second_invariant': 0.5,
        }[self.strain_rate_convention]
        return (factor * self.A**(-1 / self.n) * grain**(self.p / self.n)
                * fugacity**(-self.r / self.n) * rate**((1 - self.n) / self.n)
                * np.exp((self.E + pres * self.V) / (self.n * _GAS_CONSTANT * temp)))


@dataclass(frozen=True)
class AspectFlowLaw:
    """SI power-law coefficients for ASPECT's visco-plastic viscosity.

    Fugacity is already folded into A. ``p`` remains explicit through grain
    size. E is J/mol, V is m**3/mol, and A is Pa**(-n) * m**p / s.
    """

    A: float
    n: float
    E: float
    V: float = 0.0
    p: float = 0.0

    def __post_init__(self):
        _positive('A', self.A)
        _positive('n', self.n)
        for name in ('E', 'V', 'p'):
            if not isfinite(getattr(self, name)):
                raise ValueError(f'{name} must be finite')

    def viscosity(self, strain_rate, temperature, pressure=0.0, *, grain_size_m=1e-3):
        """Return viscosity in Pa s for broadcastable SI inputs.

        Strain rate is edot_II in s**(-1), temperature is K and pressure is
        Pa. eta = 0.5 A**(-1/n) d**(p/n) edot_II**((1-n)/n)
        exp((E+P*V)/(n*R*T)). No plasticity or viscosity limits are applied.
        """
        rate, temp, pres, grain = np.broadcast_arrays(
            *[np.asarray(x, dtype=float) for x in
              (strain_rate, temperature, pressure, grain_size_m)]
        )
        for name, values in [('strain_rate', rate), ('temperature', temp),
                             ('grain_size_m', grain)]:
            if not np.all(np.isfinite(values) & (values > 0)):
                raise ValueError(f'{name} must be finite and positive')
        if not np.all(np.isfinite(pres)):
            raise ValueError('pressure must be finite')
        return (0.5 * self.A**(-1 / self.n) * grain**(self.p / self.n)
                * rate**((1 - self.n) / self.n)
                * np.exp((self.E + pres * self.V) / (self.n * _GAS_CONSTANT * temp)))


@dataclass(frozen=True)
class PrefactorConversion:
    """Converted law and factors retained so the conversion is auditable.

    A_aspect = experimental.A * unit_factor * strain_rate_factor
    * water_factor. Water_factor uses fugacity in Pa;
    unit_factor includes conversion of its experimental units.
    """

    experimental: ExperimentalFlowLaw
    law: AspectFlowLaw
    unit_factor: float
    strain_rate_factor: float
    water_factor: float
    water_fugacity_pa: float | None


def to_aspect(
    experimental: ExperimentalFlowLaw, *, water_fugacity_pa: float | None = None,
) -> PrefactorConversion:
    """Convert a published law into ASPECT coefficients and report factors.

    Require an explicit, positive fugacity in Pa for r != 0. Reject fugacity
    for laws without explicit water dependence, rather than imply a change
    to a wet experimental calibration.

    For uniaxial data the invariant factor is 3**((n+1)/2)/2; for engineering
    shear data it is 1/2 because edot_II = gamma_dot/2 and tau_II = tau.
    Already-invariant coefficients receive no additional factor. See
    Dannberg et al. (2017), https://doi.org/10.1002/2017GC006944, SI S1.3.
    """
    if experimental.r != 0:
        if water_fugacity_pa is None:
            raise ValueError('An explicit water fugacity in Pa is required')
        _positive('water_fugacity_pa', water_fugacity_pa)
        water_factor = water_fugacity_pa**experimental.r
    else:
        if water_fugacity_pa is not None:
            raise ValueError('This law has no explicit water fugacity dependence')
        water_factor = 1.0
    unit_factor = (
        _PRESSURE_UNITS[experimental.stress_unit]**(-experimental.n)
        * _LENGTH_UNITS[experimental.grain_size_unit]**experimental.p
        * _PRESSURE_UNITS[experimental.fugacity_unit]**(-experimental.r)
    )
    strain_factor = {
        'uniaxial': 3**((experimental.n + 1) / 2) / 2,
        'engineering_shear': 0.5,
        'second_invariant': 1.0,
    }[experimental.strain_rate_convention]
    law = AspectFlowLaw(
        A=experimental.A * unit_factor * strain_factor * water_factor,
        n=experimental.n, E=experimental.E, V=experimental.V, p=experimental.p,
    )
    return PrefactorConversion(
        experimental, law, unit_factor, strain_factor, water_factor,
        water_fugacity_pa,
    )


GLEASON_TULLIS_1995 = ExperimentalFlowLaw(
    name='Wet quartzite, no melt (Gleason and Tullis, 1995)',
    reference='https://doi.org/10.1016/0040-1951(95)00011-B',
    A=1.1e-4, n=4.0, E=223e3,
    stress_unit='MPa', grain_size_unit='um', fugacity_unit='MPa',
    strain_rate_convention='uniaxial',
    notes='Wet calibration; no explicit fugacity term. Water content is not fugacity.',
)

RYBACKI_2006 = ExperimentalFlowLaw(
    name='Wet anorthite (Rybacki et al., 2006), cookbook parameterization',
    reference='https://doi.org/10.1029/2005JB003663',
    A=10**0.2, n=3.0, E=345e3, r=1.0,
    stress_unit='MPa', grain_size_unit='um', fugacity_unit='MPa',
    strain_rate_convention='uniaxial',
    notes='ASPECT continental extension choice V=0; fugacity must be supplied. '
          'This is the cookbook parameterization, not every experimental fit.',
)
