"""Parameters of the analytic model, read from model.yaml (N(E) from nmuons.yaml)."""
from pathlib import Path
import yaml

YEAR = 60 * 60 * 24 * 365      # s

def numbers(v):
    """Floats all the way down (YAML 1.1 reads 1e18 as text)."""
    if isinstance(v, dict):
        return {k: numbers(x) for k, x in v.items()}
    if isinstance(v, list):
        return [numbers(x) for x in v]
    return float(v)

def load(path=Path(__file__).with_name("model.yaml")):
    """A YAML file of numbers, lists of numbers, or blocks of them."""
    return numbers(yaml.safe_load(Path(path).read_text()))

par = load()
alpha, gamma, epsilon = par["alpha"], par["gamma"], par["epsilon"]
mu = load(Path(__file__).with_name("nmuons.yaml"))
beta, eta = mu["beta"], mu["eta"]
lmbda = par["lambda"]          # lambda is a Python keyword
C = par["C"]
phi_D = par["phi_D"]
mu_flux = par["mu_flux"]
n_phones, A_phone, dt_phone = int(par["n_phones"]), par["phone_area"], par["phone_window"]
n_taggers, A_tagger, dt_tagger = int(par["n_taggers"]), par["tagger_area"], par["tagger_window"]
