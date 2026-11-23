import matplotlib.pyplot as plt
from pathlib import Path

OUT_DIR = Path("project_1_equals_2/math_assets")
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams['mathtext.fontset'] = 'cm'

FORMULAS = [
    ("eq_1", r"$a = b$"),
    ("eq_2", r"$a^2 = a \cdot b$"),
    ("eq_3", r"$a^2 - b^2 = a b - b^2$"),
    ("eq_4", r"$(a - b)(a + b) = b(a - b)$"),
    ("eq_5", r"$\frac{(a - b)(a + b)}{a - b} = \frac{b(a - b)}{a - b}$"),
    ("eq_6", r"$a + b = b \quad \Longrightarrow \quad 2b = b$"),
    ("eq_7", r"$\mathbf{2 = 1 \quad (!?)}$"),
    ("eq_8", r"$\mathbf{a - b = 0 \quad (Division\ by\ 0!)}$"),
    ("eq_9", r"$\mathbf{\frac{x}{0} \quad (Undefined!)}$"),
    ("eq_10", r"$\mathbf{1 \neq 2 \quad (Q.E.D)}$")
]

for name, formula in FORMULAS:
    fig, ax = plt.subplots(figsize=(6, 1.4), dpi=220)
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    ax.axis('off')
    
    color = '#D93025' if any(k in formula for k in ['(!?)', 'Division', 'Undefined']) else '#111316'
    
    ax.text(0.5, 0.5, formula, fontsize=26, ha='center', va='center', color=color)
    out_file = OUT_DIR / f"{name}.png"
    plt.savefig(out_file, bbox_inches='tight', transparent=True, pad_inches=0.1)
    plt.close(fig)
    print(f"Generated {out_file.name}")

print("All LaTeX formulas rendered successfully!")
