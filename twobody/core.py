"""
Celestial mechanics.

General comments
----------------
- Parameterization comes from Winn http://arxiv.org/abs/1001.2010
- Mean, eccentric, and true anomaly formulae from Wikipedia
  https://en.wikipedia.org/wiki/Eccentric_anomaly

"""

# Standard library
import warnings

# Third-party
import astropy.units as u
import numpy as np
au_per_day_m_s = (1*u.m/u.s*u.day).to(u.au).value

__all__ = ['mean_anomaly_from_eccentric_anomaly',
           'eccentric_anomaly_from_mean_anomaly',
           'true_anomaly_from_eccentric_anomaly',
           'd_eccentric_anomaly_d_mean_anomaly',
           'd_true_anomaly_d_eccentric_anomaly',
           'Z_from_elements', 'rv_from_elements']

from .wrap import (_mean_anomaly_from_eccentric_anomaly,
                   _eccentric_anomaly_from_mean_anomaly_Newton1)

def mean_anomaly_from_eccentric_anomaly(E, e):
    """
    Parameters
    ----------
    E : numeric, array_like [radian]
        Eccentric anomaly.
    e : numeric, array_like
        Eccentricity.

    Returns
    -------
    Ms : numeric, array_like [radian]
        Mean anomaly.
    """
    # TODO: contiguous, 1D, etc.
    return _mean_anomaly_from_eccentric_anomaly(E, e)

def eccentric_anomaly_from_mean_anomaly(M, e, tol=1E-10, maxiter=128):
    """
    Parameters
    ----------
    M : numeric, array_like [radian]
        Mean anomaly.
    e : numeric
        Eccentricity.
    tol : numeric (optional)
        Numerical tolerance used in iteratively solving for eccentric anomaly.
    maxiter : int (optional)
        Maximum number of iterations when iteratively solving for
        eccentric anomaly.

    Returns
    -------
    E : numeric [radian]
        Eccentric anomaly.

    Issues
    ------
    - Magic numbers ``tol`` and ``maxiter``
    """
    # TODO: contiguous, 1D, etc.
    return _eccentric_anomaly_from_mean_anomaly_Newton1(M, e, tol, maxiter)

def true_anomaly_from_eccentric_anomaly(Es, e):
    """
    Parameters
    ----------
    Es : numeric, array_like [radian]
        Eccentric anomaly.
    e : numeric, array_like
        Eccentricity.

    Returns
    -------
    fs : numeric [radian]
        True anomaly.
    """
    cEs, sEs = np.cos(Es), np.sin(Es)
    fs = np.arccos((cEs - e) / (1.0 - e * cEs))
    return fs * np.sign(np.sin(fs)) * np.sign(sEs)

def d_eccentric_anomaly_d_mean_anomaly(Es, e):
    """
    Parameters
    ----------
    Es : numeric, array_like [radian]
        Eccentric anomaly.
    e : numeric, array_like
        Eccentricity.

    Returns
    -------
    dE_dM : numeric
        Derivatives of one anomaly w.r.t. the other.
    """
    return 1. / (1. - e * np.cos(Es))

def d_true_anomaly_d_eccentric_anomaly(Es, fs, e):
    """
    Parameters
    ----------
    Es : numeric, array_like [radian]
        Eccentric anomaly.
    fs : numeric, array_like [radian]
        True anomaly.
    e : numeric, array_like
        Eccentricity.

    Returns
    -------
    df_dE : numeric
        Derivatives of one anomaly w.r.t. the other.

    Issues
    ------
    - Insane assert statement.
    """
    cfs, sfs = np.cos(fs), np.sin(fs)
    cEs, sEs = np.cos(Es), np.sin(Es)
    assert np.allclose(cEs, (e + cfs) / (1. + e * cfs))
    return (sEs / sfs) * (1. + e * cfs) / (1. - e * cEs)

def Z_from_elements(times, P, K, e, omega, time0):
    """
    Z points towards the observer.

    Parameters
    ----------
    times : array_like [day]
        BJD of observations.
    p : numeric [day]
        Period.
    K : numeric [m/s]
        Velocity semi-amplitude.
    e : numeric
        Eccentricity.
    omega : numeric [radian]
        Perihelion argument parameter from Winn.
    time0 : numeric [day]
        Time of "zeroth" pericenter.

    Returns
    -------
    Z : numeric [AU]
        Line-of-sight position.

    Issues
    ------
    - doesn't include system Z value (Z offset or Z zeropoint)
    - could be made more efficient (there are lots of re-dos of trig calls)

    """
    times = np.array(times)

    dMdt = 2. * np.pi / P
    Ms = (times - time0) * dMdt

    Es = eccentric_anomaly_from_mean_anomaly(Ms, e)
    fs = true_anomaly_from_eccentric_anomaly(Es, e)

    a1sini = K/(2*np.pi) * (P * np.sqrt(1-e**2)) * au_per_day_m_s
    rs = a1sini * (1. - e * np.cos(Es))
    # this is equivalent to:
    # rs = asini * (1. - e**2) / (1 + e*np.cos(fs))

    return rs * np.sin(omega + fs)

def rv_from_elements(times, P, K, e, omega, phi0, anomaly_tol=1E-13):
    """
    Parameters
    ----------
    times : array_like [day]
        Usually: Barycentric MJD of observations. But the epoch (t=0)
        is arbitrary and up to the user to keep track of.
    p : numeric [day]
        Period.
    K : numeric [m/s]
        Velocity semi-amplitude.
    e : numeric
        Eccentricity.
    omega : numeric [radian]
        Argument of periastron.
    phi0 : numeric [radian]
        Phase at pericenter relative to t=0.
    anomaly_tol : numeric (optional)
        Tolerance passed to
        `~thejoker.celestialmechanics.celestialmechanics.eccentric_anomaly_from_mean_anomaly` for
        solving for the eccentric anomaly.

    Returns
    -------
    rv : numeric [m/s]
        Relative radial velocity - does not include systemtic velocity!

    Issues
    ------
    - could be made more efficient (there are lots of re-dos of trig calls)
    """
    times = np.array(times)
    Ms = (2 * np.pi * times / P) - phi0

    Es = eccentric_anomaly_from_mean_anomaly(Ms, e, tol=anomaly_tol)
    fs = true_anomaly_from_eccentric_anomaly(Es, e)
    vz = K * (np.cos(omega + fs) + e*np.cos(omega))

    return vz
