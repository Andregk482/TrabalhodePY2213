import numpy as np
import pandas as pd


def fmt(x, casas=None):
    """Formato brasileiro: 1.234.567,89"""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "-"
    if casas is None:
        casas = 0 if abs(x) >= 1000 else 2
    t = f"{x:,.{casas}f}"
    return t.replace(",", "§").replace(".", ",").replace("§", ".")


def descritiva(valores, populacional=True):
    s = pd.Series(valores, dtype="float").dropna()
    n = len(s)
    if n == 0:
        return None
    ddof = 0 if populacional else 1
    q1, med, q3 = (float(s.quantile(p)) for p in (0.25, 0.5, 0.75))
    iqr = q3 - q1
    lim_inf, lim_sup = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    media = float(s.mean())
    var = float(s.var(ddof=ddof)) if n > ddof else np.nan
    dp = float(np.sqrt(var)) if not np.isnan(var) else np.nan
    cv = dp / abs(media) * 100 if media != 0 and not np.isnan(dp) else np.nan
    vc = s.round(2).value_counts()
    topo = vc[vc == vc.max()]
    modas = sorted(topo.index) if vc.max() > 1 and len(topo) < len(vc) else []
    return {
        "n": n, "media": media, "mediana": med, "modas": modas,
        "q1": q1, "q3": q3, "iqr": iqr, "minimo": float(s.min()), "maximo": float(s.max()),
        "amplitude": float(s.max() - s.min()), "variancia": var, "desvio": dp, "cv": cv,
        "lim_inf": lim_inf, "lim_sup": lim_sup,
        "mask_outlier": (s < lim_inf) | (s > lim_sup),
    }


def interpretar(d, rotulos, valores, unidade=""):
    """Texto de leitura estatistica gerado a partir dos numeros."""
    u = "%" if unidade == "%" else (f" {unidade}" if unidade else "")
    s = pd.Series(list(valores), dtype="float").reset_index(drop=True)
    r = pd.Series(list(rotulos)).reset_index(drop=True)
    ok = s.notna()
    s, r = s[ok].reset_index(drop=True), r[ok].reset_index(drop=True)
    txt = []
    dif = (d["media"] - d["mediana"]) / abs(d["mediana"]) * 100 if d["mediana"] else 0
    if abs(dif) < 5:
        txt.append(f"Média ({fmt(d['media'])}) e mediana ({fmt(d['mediana'])}) estão próximas "
                   f"(diferença de {fmt(abs(dif), 1)}%): a distribuição é aproximadamente simétrica e a média representa bem o conjunto.")
    elif dif > 0:
        txt.append(f"A média ({fmt(d['media'])}) está {fmt(dif, 1)}% acima da mediana ({fmt(d['mediana'])}): "
                   "há assimetria à direita, valores muito altos puxam a média para cima. A mediana é a melhor referência do valor típico.")
    else:
        txt.append(f"A média ({fmt(d['media'])}) está {fmt(abs(dif), 1)}% abaixo da mediana ({fmt(d['mediana'])}): "
                   "há assimetria à esquerda, valores muito baixos puxam a média para baixo.")
    txt.append(f"A metade central dos dados está entre Q1 = {fmt(d['q1'])} e Q3 = {fmt(d['q3'])}, "
               f"um intervalo interquartil de {fmt(d['iqr'])}{u}.")
    if not np.isnan(d["cv"]):
        nivel = "baixa" if d["cv"] < 15 else "moderada" if d["cv"] < 30 else "alta"
        txt.append(f"O coeficiente de variação é {fmt(d['cv'], 1)}%, dispersão {nivel} em relação à média.")
    out = r[d["mask_outlier"].reset_index(drop=True)] if len(r) == len(d["mask_outlier"]) else []
    if len(out):
        txt.append(f"Pela regra de 1,5 x IQR, são outliers: {', '.join(map(str, out))}. "
                   f"Limites: {fmt(d['lim_inf'])} e {fmt(d['lim_sup'])}.")
    else:
        txt.append(f"Nenhum outlier pela regra de 1,5 x IQR (limites {fmt(d['lim_inf'])} e {fmt(d['lim_sup'])}).")
    if len(s) > 1:
        imax, imin = s.idxmax(), s.idxmin()
        txt.append(f"Maior valor: {r[imax]} ({fmt(s[imax])}). Menor valor: {r[imin]} ({fmt(s[imin])}). "
                   f"Amplitude: {fmt(d['amplitude'])}{u}.")
    return txt
