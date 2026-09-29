"""
deck/equations.py
=================
Render the project's mathematics as transparent PNGs for the slides.

PowerPoint has no good way to typeset mathematics from a script, and monospace text
does not read as an equation. matplotlib's mathtext engine renders LaTeX-style markup
without needing a TeX installation, which gives formulas that look like the ones in the
paper.

Each entry is numbered to match either the source paper's equation numbers (so the
audience can follow along in the PDF) or our own derivation.

Run:  python deck/equations.py
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# 'stix' is a Times-compatible math font, so equations match the body text.
matplotlib.rcParams['mathtext.fontset'] = 'stix'
matplotlib.rcParams['font.family'] = 'STIXGeneral'

OUT = os.path.join("figures", "equations")
# Black, to match the reference deck's monochrome Times New Roman styling.
INK = "#000000"

# name -> (latex, fontsize). Transparent background, tight bounds.
EQUATIONS = {
    # ---- the paper's feature-selection objectives -------------------------------
    # Paper eq. (5): recursive feature elimination, averaged over m estimators.
    "eq5_rfe": (
        r"$\hat{y}\;=\;\frac{1}{m}\sum_{j=1}^{m}\sum_{i=1}^{n}W_j(x_i,x')\,y_i"
        r"\;=\;\sum_{i=1}^{n}\left(\frac{1}{m}\sum_{j=1}^{m}W_j(x_i,x')\right)y_i$", 22),

    # Paper eq. (6): the Lasso objective - squared error plus an L1 shrinkage penalty.
    "eq6_lasso": (
        r"$J_\beta(\beta)\;=\;\frac{1}{N}\sum_{i=1}^{N}\left(Y_i-\hat{Y}_i\right)^{2}"
        r"\;+\;\lambda\sum_{j=1}^{p}\left|\hat{\beta}_j\right|$", 22),

    # ---- the Choquet machinery ---------------------------------------------------
    "sugeno_union": (
        r"$g(A\cup B)\;=\;g(A)+g(B)+\lambda\,g(A)\,g(B)$", 22),

    "sugeno_lambda": (
        r"$1+\lambda\;=\;\prod_{i=1}^{N}\left(1+\lambda\,g_i\right)$", 22),

    "choquet": (
        r"$C\;=\;\sum_{j=1}^{N} h_{(j)}\left[\,g\!\left(A_j\right)-g\!\left(A_{j-1}\right)\right]$"
        "\n"
        r"$\mathrm{where}\;\;h_{(1)}\geq h_{(2)}\geq\cdots\geq h_{(N)},\;\;A_j=\{x_{(1)},\dots,x_{(j)}\}$", 20),

    # ---- our degeneracy result ----------------------------------------------------
    "degeneracy": (
        r"$g_i=g\;\;\forall i\;\;\Longrightarrow\;\;"
        r"g(A_j)=\frac{(1+\lambda g)^{\,j}-1}{\lambda}$"
        "\n\n"
        r"$w_j\;=\;g(A_j)-g(A_{j-1})\;=\;g\,\beta^{\,j-1},\qquad \beta=1+\lambda g$"
        "\n\n"
        r"$\sum_{j=1}^{N} w_j\;=\;\frac{g\left(\beta^{N}-1\right)}{\beta-1}"
        r"\;=\;\frac{\beta^{N}-1}{\lambda}\;=\;g(X)\;=\;1$", 19),

    "degeneracy_limit": (
        r"$\sum_i g_i<1\;\Rightarrow\;\lambda>0\;\Rightarrow\;\beta>1"
        r"\;\Rightarrow\;w_j\;\mathrm{increases\;with}\;j$"
        "\n\n"
        r"$\lim_{g\to 0} C \;=\; \min\left(h_1,h_2,\dots,h_N\right)$", 20),

    # ---- feature definitions ------------------------------------------------------
    "hjorth": (
        r"$\mathrm{Mobility}(x)=\sqrt{\dfrac{\mathrm{var}(x')}{\mathrm{var}(x)}}"
        r"\qquad\mathrm{Complexity}(x)=\dfrac{\mathrm{Mobility}(x')}{\mathrm{Mobility}(x)}$", 20),

    "entropy": (
        r"$SE=-\sum_i p_i\log_2 p_i\qquad"
        r"CD=\lim_{r\to 0}\frac{\partial\log C(r)}{\partial\log r}$", 21),

    "qtc": (
        r"$QTc=\dfrac{QT}{\sqrt{RR}}\qquad"
        r"\mathrm{RMSSD}=\sqrt{\overline{\left(RR_{i+1}-RR_i\right)^{2}}}$", 21),

    # ---- assessment metrics -------------------------------------------------------
    "metrics": (
        r"$\mathrm{RMSE}=\sqrt{\overline{\left(\hat{y}-y\right)^{2}}}\qquad"
        r"\mathrm{MARD}=\overline{\left|\dfrac{\hat{y}-y}{y}\right|}\times 100\%$"
        "\n\n"
        r"$R^{2}=1-\dfrac{\sum\left(\hat{y}-y\right)^{2}}{\sum\left(\bar{y}-y\right)^{2}}"
        r"\qquad R^{2}\leq 0 \;\Leftrightarrow\; \mathrm{no\;better\;than\;the\;mean}$", 19),
}


def render(name, latex, size):
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, latex, fontsize=size, color=INK,
             horizontalalignment="left", verticalalignment="bottom")
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f"{name}.png")
    # transparent so the equation sits on whatever the slide background is
    fig.savefig(path, dpi=260, bbox_inches="tight", pad_inches=0.06, transparent=True)
    plt.close(fig)
    from PIL import Image
    w, h = Image.open(path).size
    return path, w, h


if __name__ == "__main__":
    print("Rendering equations:")
    for name, (latex, size) in EQUATIONS.items():
        p, w, h = render(name, latex, size)
        print(f"   {p}   {w}x{h}px   aspect {w/h:.2f}")
    print(f"\nDone. {len(EQUATIONS)} equations in {OUT}/")
