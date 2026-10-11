"""Generate the reference figure for the home Ka lab and print the expected
pH readings quoted in the lab's Reference section.

Model: gravimetric titration with 0.100 mol/kg NaOH (1 g of solution taken as
1 mL). Thermodynamic pKa values at 25 C with Davies activity coefficients, so
the curves show the pH a calibrated probe would read in the actual mixture.

  acetic acid : pKa = 4.756  (Harned and Ehlers 1933)
  oxalic acid : pKa1 = 1.25, pKa2 = 4.27 (Martell and Smith 1977, I = 0)

Run:  python3 make_figures.py   -> writes titration-curves.png next to this file
"""
import math
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

A_DH = 0.509          # Debye-Huckel constant, 25 C
KW = 1.0e-14
TITRANT = 0.100e-3    # mol NaOH per g of titrant solution

PKA_ACETIC = 4.756
PKA1_OX, PKA2_OX = 1.25, 4.27


def log_gamma(z, I):
    """Davies equation."""
    s = math.sqrt(I)
    return -A_DH * z * z * (s / (1 + s) - 0.3 * I)


def ph_monoprotic(n_acid, m_water, m_t, pka):
    """pH (activity scale) of a monoprotic weak acid after adding m_t g titrant."""
    V = (m_water + m_t) / 1000.0        # L
    Ca = n_acid / V
    Na = TITRANT * m_t / V
    Ka = 10 ** -pka
    I = 0.5 * Na                          # starting guess
    h = 1e-5
    for _ in range(200):
        g1 = 10 ** log_gamma(1, I)
        Kac = Ka / g1 ** 2
        Kwc = KW / g1 ** 2
        # charge balance: Na + H = A- + OH-
        def resid(h):
            a = Ca * Kac / (Kac + h)
            return Na + h - a - Kwc / h
        lo, hi = 1e-14, 1.0
        for _ in range(200):
            mid = math.sqrt(lo * hi)
            if resid(mid) > 0:
                hi = mid
            else:
                lo = mid
        h = math.sqrt(lo * hi)
        a = Ca * Kac / (Kac + h)
        I_new = 0.5 * (Na + h + a + Kwc / h)
        if abs(I_new - I) < 1e-9:
            I = I_new
            break
        I = I_new
    return -math.log10(h * 10 ** log_gamma(1, I))


def ph_diprotic(n_acid, m_water, m_t, pka1, pka2):
    V = (m_water + m_t) / 1000.0
    Ca = n_acid / V
    Na = TITRANT * m_t / V
    K1, K2 = 10 ** -pka1, 10 ** -pka2
    I = 0.5 * Na + 0.05
    h = 1e-3
    for _ in range(200):
        g1 = 10 ** log_gamma(1, I)
        g2 = 10 ** log_gamma(2, I)
        K1c = K1 / g1 ** 2
        K2c = K2 / g2
        Kwc = KW / g1 ** 2

        def species(h):
            d = h * h + K1c * h + K1c * K2c
            return Ca * K1c * h / d, Ca * K1c * K2c / d   # [HA-], [A2-]

        def resid(h):
            ha, a2 = species(h)
            return Na + h - ha - 2 * a2 - Kwc / h
        lo, hi = 1e-14, 1.0
        for _ in range(200):
            mid = math.sqrt(lo * hi)
            if resid(mid) > 0:
                hi = mid
            else:
                lo = mid
        h = math.sqrt(lo * hi)
        ha, a2 = species(h)
        I_new = 0.5 * (Na + h + ha + 4 * a2 + Kwc / h)
        if abs(I_new - I) < 1e-9:
            I = I_new
            break
        I = I_new
    return -math.log10(h * 10 ** log_gamma(1, I))


# ---- lab conditions -------------------------------------------------------
# Acetic acid: 1.50 g of 5.0 % vinegar (0.075 g, 1.249 mmol) in 20 g water.
N_ACETIC = 0.075 / 60.05
M_W_ACETIC = 21.5
M_EQ_ACETIC = N_ACETIC / TITRANT

# Oxalic acid: 15 g of extract from 2.0 g Bar Keepers Friend (8.5 % oxalic
# acid) in 60 g water, roughly 0.17 g / 90.03 = 1.89 mmol per 60 g,
# i.e. about 0.47 mmol in a 15 g portion.
N_OX = 0.17 / 90.03 * 15 / 60
M_W_OX = 15.0
M_EQ_OX = 2 * N_OX / TITRANT

if __name__ == "__main__":
    f = np.linspace(0.0, 1.25, 600)
    ph_ac = [ph_monoprotic(N_ACETIC, M_W_ACETIC, fi * M_EQ_ACETIC, PKA_ACETIC) for fi in f]
    ph_ox = [ph_diprotic(N_OX, M_W_OX, fi * M_EQ_OX, PKA1_OX, PKA2_OX) for fi in f]

    marks_ac = [0.25, 0.50, 0.75]
    marks_ox = [0.625, 0.75, 0.875]

    print("Equivalence titrant masses: acetic %.2f g, oxalic %.2f g" % (M_EQ_ACETIC, M_EQ_OX))
    print("Expected readings (activity pH):")
    for fi in marks_ac:
        print("  acetic  f=%.3f  pH=%.2f" % (fi, ph_monoprotic(N_ACETIC, M_W_ACETIC, fi * M_EQ_ACETIC, PKA_ACETIC)))
    for fi in marks_ox:
        print("  oxalic  f=%.3f  pH=%.2f" % (fi, ph_diprotic(N_OX, M_W_OX, fi * M_EQ_OX, PKA1_OX, PKA2_OX)))
    print("  acetic  f=1.000  pH=%.2f" % ph_monoprotic(N_ACETIC, M_W_ACETIC, M_EQ_ACETIC, PKA_ACETIC))
    print("  oxalic  f=1.000  pH=%.2f" % ph_diprotic(N_OX, M_W_OX, M_EQ_OX, PKA1_OX, PKA2_OX))

    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.9), sharey=True)
    for ax, ph, marks, name in (
        (axes[0], ph_ac, marks_ac, "Acetic acid (vinegar)"),
        (axes[1], ph_ox, marks_ox, "Oxalic acid (cleanser extract)"),
    ):
        ax.axhspan(7.4, 8.6, color="#f4c542", alpha=0.25, lw=0, label="turmeric changes color")
        ax.plot(f, ph, color="#1f2a37", lw=1.8)
        for fi in marks:
            p = ph[np.argmin(abs(f - fi))]
            ax.plot([fi], [p], "o", color="#b3412f", ms=5)
            ax.annotate("f = %g" % fi, (fi, p), xytext=(6, -12), textcoords="offset points", fontsize=8, color="#b3412f")
        ax.axvline(1.0, color="#5b6470", lw=0.8, ls="--")
        ax.set_xlim(0, 1.25)
        ax.set_ylim(0, 13)
        ax.set_xticks(np.arange(0, 1.26, 0.25))
        ax.set_yticks(range(0, 14, 1))
        ax.grid(True, which="major", color="#d8dce2", lw=0.6)
        ax.set_xlabel("fraction of equivalence titrant, f")
        ax.set_title(name, fontsize=10)
    axes[0].set_ylabel("pH")
    axes[0].legend(loc="upper left", fontsize=8, frameon=False)
    fig.tight_layout()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "titration-curves.png")
    fig.savefig(out, dpi=200)
    print("wrote", out)
