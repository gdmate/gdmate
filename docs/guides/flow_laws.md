# Experimental flow laws and ASPECT coefficients

Use `gdmate.rheology_models.flow_laws` to keep published parameters separate
from model assumptions. Three reusable records support this workflow:

- `ExperimentalFlowLaw` records coefficients, their units, the experimental
  strain-rate/stress convention, a source reference, and notes.
- `to_aspect()` converts units and strain-rate conventions, folds an explicitly
  supplied constant water fugacity into A. It returns a `PrefactorConversion`
  containing all conversion factors
  and the original record, making the calculation auditable.
- `AspectFlowLaw` holds the derived SI coefficients and evaluates dislocation
  viscosity for scalar or broadcastable array inputs.

```python
from dataclasses import asdict

from gdmate.rheology_models.flow_laws import (
    GLEASON_TULLIS_1995, RYBACKI_2006, to_aspect,
)

upper = to_aspect(GLEASON_TULLIS_1995)
lower = to_aspect(RYBACKI_2006, water_fugacity_pa=1e6)
print(upper.law.A)  # approximately 8.57e-28 Pa^-4 s^-1
print(lower.law.A)  # approximately 7.13e-18 Pa^-3 s^-1
viscosity = upper.law.viscosity(1e-15, 800, pressure=1e9)
audit_record = asdict(upper)  # JSON-serializable coefficients and assumptions
```

## Units and conventions

When creating an `ExperimentalFlowLaw`, explicitly supply `stress_unit`,
`grain_size_unit`, `fugacity_unit` and `strain_rate_convention` as keyword
arguments. They have no defaults, even for zero grain-size or fugacity exponents.
For example:

```python
from gdmate.rheology_models.flow_laws import ExperimentalFlowLaw

quartzite = ExperimentalFlowLaw(
    name="Wet quartzite, no melt (Gleason and Tullis, 1995)",
    reference="https://doi.org/10.1016/0040-1951(95)00011-B",
    A=1.1e-4, n=4.0, E=223e3,
    stress_unit="MPa", grain_size_unit="um", fugacity_unit="MPa",
    strain_rate_convention="uniaxial",
)
```

The experimental equation is `edot = A * stress**n * d**(-p) * f**r *
exp(-(E+P*V)/(R*T))`. Strain rates are in inverse seconds. E is always J/mol
and V is always m³/mol. Supported experimental stress and fugacity units are
`Pa` and `MPa`; supported grain-size units are `m` and `um`. Supply fugacity to
`to_aspect()` in **Pa**, irrespective of the experimental record's units.
The converted coefficients retain grain-size dependence: the viscosity method
accepts grain size in metres (default 1 mm).

The strain-rate convention must match the published equation:

| Record convention | Experimental rate and stress | Prefactor factor |
| --- | --- | --- |
| `uniaxial` | axial rate, differential stress | `3**((n+1)/2)/2` |
| `engineering_shear` | engineering shear rate gamma_dot, shear stress | `1/2` |
| `second_invariant` | strain-rate invariant, deviatoric stress invariant | `1` |

Calling all experimental rates “shear strain rate” loses this distinction.
The quartzite and anorthite records use the uniaxial conversion adopted by
ASPECT's continental extension cookbook. Converted coefficients must not
receive this factor a second time: use `AspectFlowLaw` for already-converted
values, or label an experimental record `second_invariant` if applicable.

If U is the SI size of each experimental unit, conversion gives
`A_aspect = A_exp * U_stress**(-n) * U_length**p * U_fugacity**(-r)
* strain_rate_factor * fugacity_pa**r`.
For an r=0 law the water factor is one and a supplied fugacity is rejected.

## Evaluate the original experimental law

`ExperimentalFlowLaw.viscosity()` uses the recorded experimental strain-rate
convention and units. Strain rate is in s⁻¹, grain size uses `grain_size_unit`,
and water fugacity uses `fugacity_unit`. **Pressure always uses Pa and
temperature always uses K.** Grain size is required when p is nonzero; fugacity
is required when r is nonzero. Scalars and broadcastable arrays are supported.

```python
# The anorthite record uses MPa for fugacity and stress.
eta_mpa_s = RYBACKI_2006.viscosity(
    strain_rate=1e-15, temperature=900, pressure=1e9,
    water_fugacity=1.0,  # MPa, not Pa
)
eta_pa_s = eta_mpa_s * 1e6
```

The returned viscosity has units `stress_unit * s`: MPa s for the built-in
experimental records, unlike `AspectFlowLaw.viscosity()`, which returns Pa s.
The rate input also differs: for uniaxial data, supply the axial rate rather
than ASPECT's invariant. To compare at the same deformation, use
`edot_II = sqrt(3)/2 * axial_rate` for the converted ASPECT law.

Constitutive viscosity is differential stress divided by three times the axial
rate for uniaxial experiments, shear stress divided by engineering shear rate
for shear experiments, and stress invariant divided by twice the rate invariant
for invariant laws. These definitions give the same physical viscosity after
unit and rate conversion; the uniaxial result is not extensional viscosity.

## Water dependence and strength profiles

`GLEASON_TULLIS_1995` is the wet quartzite, no-melt calibration with n=4,
E=223 kJ/mol and V=0. There is **no explicit fugacity term**. Water content
is not converted to fugacity, and changing a water-content label cannot
change this law's A.

`RYBACKI_2006` records the wet anorthite parameterization used in the cookbook:
n=3, E=345 kJ/mol, V=0 and r=1. It is not a complete catalogue of the paper's
fits. An explicit water fugacity is required; 1 MPa reproduces the cookbook.

The derived ASPECT prefactors are approximately `8.57e-28` for quartzite and
`7.13e-18` for anorthite at 1 MPa water fugacity. Conversions retain full
precision and account for units, strain-rate conventions and explicit water
dependence.

See [the strength-profile notebook](../notebooks/continental_strength.ipynb)
for an illustrative continental profile with a conductive geotherm, explicit
layer boundaries and 2-D plastic yielding. Replace the pressure and temperature
arrays to evaluate other profiles. Diffusion and Peierls creep, weakening,
phase transitions and viscosity bounds are omitted.

## Sources

- [Gleason and Tullis (1995)](https://doi.org/10.1016/0040-1951(95)00011-B).
- [Rybacki et al. (2006)](https://doi.org/10.1029/2005JB003663).
- [Dannberg et al. (2017), supporting information S1.3](https://doi.org/10.1002/2017GC006944).
- ASPECT `cookbooks/continental_extension/continental_extension_rheology.py`
  and `continental_extension.prm` for the cookbook choices and conversion.
