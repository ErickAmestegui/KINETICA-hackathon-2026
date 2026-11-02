"""Right/open assembly. O=(0,0), +x slider axis, +y up, CCW radians.

Lengths in arbitrary common units; never imply physical scale from pixels.
Full rotation requires L > r + abs(e); singular equality is rejected.
"""
import math
import numpy as np
from scipy.optimize import least_squares
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Parameters(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, extra="forbid")
    r: float = Field(default=32, gt=0, le=10000)
    L: float = Field(default=128, gt=0, le=50000)
    rpm: float = Field(default=40, ge=-600, le=600)
    e: float = Field(default=0, ge=-10000, le=10000)
    phase: float = Field(default=0, ge=-100, le=100)

    @model_validator(mode="after")
    def geometry(self):
        if self.L <= self.r + abs(self.e):
            raise ValueError("Full rotation requires L > r + |e| (singular equality excluded)")
        return self


def solve(p: Parameters, t: float):
    if not math.isfinite(t):
        raise ValueError("Time must be finite")
    theta = p.phase + t * p.rpm * math.tau / 60
    a = np.array([p.r * math.cos(theta), p.r * math.sin(theta)])
    q = p.e - a[1]
    h = math.sqrt(p.L**2 - q**2)
    x = a[0] + h
    velocity = (-p.r * math.sin(theta) + q * p.r * math.cos(theta) / h) * p.rpm * math.tau / 60
    return {"t": t, "theta": theta, "O": [0., 0.], "A": a.tolist(), "B": [x, p.e], "velocity": velocity,
            "rod_error": abs(float(np.linalg.norm(np.array([x, p.e])-a))-p.L)}


class Observation(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, extra="forbid")
    frame: int = Field(ge=0)
    t: float = Field(ge=0)
    x: float
    y: float
    joint: str = Field(pattern="^(crank|slider)$")
    source: str = Field(pattern="^(manual|opencv-lk|synthetic)$")
    split: str = Field(default="validation", pattern="^(fit|validation)$")


class Calibration(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, extra="forbid")
    ox: float = 0
    oy: float = 0
    angle: float = 0  # image-space clockwise radians
    scale: float = Field(default=1, gt=0, le=100000)  # pixels per model unit
    unit: str = Field(default="relative", pattern="^(relative|mm)$")


def project(point, c: Calibration):
    x, y = point
    co, si = math.cos(c.angle), math.sin(c.angle)
    return np.array([c.ox+c.scale*(co*x+si*y), c.oy+c.scale*(si*x-co*y)])


def compare(p, observations, c, trained_frames=()):
    rows = []
    for o in observations:
        point = solve(p, o.t)["A" if o.joint == "crank" else "B"]
        predicted = project(point, c)
        residual = float(np.linalg.norm(predicted-np.array([o.x, o.y])))
        rows.append({**o.model_dump(), "predicted_x": float(predicted[0]), "predicted_y": float(predicted[1]), "error_px": residual})
    def metrics(split):
        subset = [row for row in rows if row['split'] == split]
        errors = np.array([row["error_px"] for row in subset])
        contaminated = split == 'validation' and any(row['frame'] in trained_frames for row in subset)
        return {"n": len(errors), "rmse_px": float(np.sqrt(np.mean(errors**2))) if len(errors) and not contaminated else None,
                "max_px": float(np.max(errors)) if len(errors) and not contaminated else None,
                "reason": 'Validation includes frames previously used for fitting; refit first' if contaminated else None if len(errors) else 'No observations in this split'}
    return {"rows": rows, "fit": metrics("fit"), "validation": metrics("validation"),
            "units": "pixels", "physical_scale_user_declared": c.unit == "mm"}


def fit_parameters(initial, observations, calibration):
    train = [o for o in observations if o.split == "fit"]
    if len(train) < 12 or len({o.frame for o in train}) < 8:
        raise ValueError("Need at least 12 fit observations over 8 distinct frames")
    if {o.joint for o in train} != {"crank", "slider"}:
        raise ValueError("Fit requires both crank and slider centers; scale/origin/axis must be calibrated")
    if any(o.source == "synthetic" for o in train) and any(o.source != "synthetic" for o in observations):
        raise ValueError("Do not mix synthetic and real observations")
    span = max(o.t for o in train)-min(o.t for o in train)
    if span * abs(initial.rpm) / 60 < 0.7:
        raise ValueError("Observations must span at least 0.7 revolution at the initial speed")
    def decode(v):
        return Parameters(r=v[0], L=v[0]+abs(initial.e)+v[1], rpm=v[2], phase=v[3], e=initial.e)
    def residual(v):
        p = decode(v)
        return np.concatenate([project(solve(p, o.t)["A" if o.joint == "crank" else "B"], calibration)-[o.x,o.y] for o in train])
    x0 = [initial.r, initial.L-initial.r-abs(initial.e), initial.rpm, initial.phase]
    result = least_squares(residual, x0, bounds=([.01,.01,-600,-100],[10000,20000,600,100]), loss="soft_l1", max_nfev=500)
    if not result.success or np.linalg.matrix_rank(result.jac) < 4:
        raise ValueError("Fit did not converge or is underdetermined; improve observations")
    p = decode(result.x)
    p.phase = (p.phase + math.pi) % math.tau - math.pi
    return {"parameters": p.model_dump(), "comparison": compare(p, observations, calibration),
            "fit_frames": sorted({o.frame for o in train}), "note": "Local least-squares solution, fixed calibration and eccentricity; validate on held-out frames."}
