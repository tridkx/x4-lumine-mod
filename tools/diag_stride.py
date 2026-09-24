# -*- coding: utf-8 -*-
"""Play a stride and a sit on the rig, and see where the feet end up.

Everything upstream is symmetric and measured: the source's leg geometry sits
on its own bones (0.97 cm), the retargeted bone chain matches the source's
attitude (3.5 deg), and every bone's vertices are on the correct side.

What is *not* symmetric with vanilla is where the leg bones ended up.  The
source's legs taper inwards (ankles 11.7 cm apart) and X4's bind pose splays
them (35.4 cm), so `LATERAL_DAMP` keeps only part of the sideways travel -- and
the current values taper *along* the chain (thigh 0.60, calf 0.30, foot 0.20),
which bends the bone chain rather than moving it.  The foot bone lands 7 cm
inside the geometry it drives; the geometry itself was built from those
targets, so the bind pose looks fine and only animation exposes it.

This script applies representative joint rotations (a walk contact pose and a
sitting pose) to the leg chain and reports the world position of the mesh that
each foot bone drives.  Comparing our rig against vanilla -- same rotations,
same code -- separates "the pose is just narrow" from "our rig swings the feet
across the midline".

    python tools/diag_stride.py
"""

import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, r"D:\dsh-x4\x4-character-retarget\tools")

#: a walk contact: front leg forward, back leg behind, slight hip drop.
#: rotations are about the bone's own local X (the hinge axis of a Biped leg),
#: in degrees -- the sign is what a mirrored rig expects, so *both* legs get
#: the same sign and a mirrored rig steps apart.
POSES = {
    'walk (L fwd 25, R back 25)': {'Bip01 L Thigh': -25.0,
                                   'Bip01 R Thigh': +25.0},
    'walk (both fwd 25)':         {'Bip01 L Thigh': -25.0,
                                   'Bip01 R Thigh': -25.0},
    'sit (thighs fwd 80, knees 80)': {'Bip01 L Thigh': -80.0,
                                      'Bip01 R Thigh': -80.0,
                                      'Bip01 L Calf': +80.0,
                                      'Bip01 R Calf': +80.0},
    'stand (bind)':               {},
}

ASSETS = [
    ('vanilla', os.path.join(HERE, '..', 'work', 'b_vanilla_body.npz')),
    ('lumine', os.path.join(HERE, '..', 'work', 'b_lumine_body.npz')),
]


def rot_x(deg):
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], float)


def load(path):
    d = np.load(path, allow_pickle=True)
    names = [str(x) for x in d['bone_names']]
    parents = [str(x) if x is not None and str(x) != 'None' else None
               for x in d['bone_parents']]
    return {
        'names': names,
        'parents': parents,
        'heads': d['bone_heads'],
        'tails': d['bone_tails'],
        'verts': d['verts'],
        'w_idx': [[str(b) for b in ix] for ix in d['w_idx']],
        'w_val': [np.asarray(v, float) for v in d['w_val']],
    }


def skin(a, pose):
    """Linear blend skinning with per-bone world rotations about the bone head.

    Only one bone moves per chain link and the bind pose is the rest pose, so
    the skinned position is the usual sum over weights of
    `R_b (v - h_b) + h_b`, with `R_b` composed down the chain.
    """
    names, parents = a['names'], a['parents']
    heads = a['heads']
    idx = {n: i for i, n in enumerate(names)}
    order = sorted(range(len(names)),
                   key=lambda i: (0 if parents[i] is None else 1))
    # accumulate each bone's world rotation: parent's R times its own
    R = {}
    for i in order:
        p = parents[i]
        own = rot_x(pose.get(names[i], 0.0))
        R[i] = own if (p is None or p not in R) else R[idx[p]] @ own
    V = a['verts'].copy()
    out = np.zeros_like(V)
    for i, (ix, wv) in enumerate(zip(a['w_idx'], a['w_val'])):
        v = V[i]
        acc = np.zeros(3)
        for b, w in zip(ix, wv):
            j = idx.get(b)
            if j is None:
                acc += w * v
                continue
            h = heads[j]
            acc += w * (R[j] @ (v - h) + h)
        out[i] = acc
    return out


def foot_report(a, label, posed):
    """Mean X/Y/Z of the mesh each foot bone drives, after posing."""
    idx = {n: i for i, n in enumerate(a['names'])}
    res = {}
    for bone in ('Bip01 L Foot', 'Bip01 R Foot', 'Bip01 L Toe0', 'Bip01 R Toe0'):
        j = idx.get(bone)
        if j is None:
            continue
        m = np.array([any(b == bone and w > 0.5 for b, w in zip(ix, wv))
                      for ix, wv in zip(a['w_idx'], a['w_val'])])
        if not m.any():
            continue
        res[bone] = posed[m].mean(axis=0)
    return res


def main():
    data = {label: load(path) for label, path in ASSETS
            if os.path.exists(path)}
    for pose_name, pose in POSES.items():
        print('== %s ==' % pose_name)
        print('   %-8s %-16s %-26s %s' % ('asset', 'bone', 'mean pos (x,y,z)',
                                          'feet span (x)'))
        for label, a in data.items():
            posed = skin(a, pose)
            rep = foot_report(a, label, posed)
            lf = rep.get('Bip01 L Foot')
            rf = rep.get('Bip01 R Foot')
            span = (np.linalg.norm(lf - rf) if lf is not None and rf is not None
                    else float('nan'))
            for bone in ('Bip01 L Foot', 'Bip01 R Foot'):
                p = rep.get(bone)
                if p is None:
                    continue
                print('   %-8s %-16s (%+7.2f,%+7.2f,%+7.2f)'
                      % (label, bone, p[0], p[1], p[2]))
            print('   %-8s %-16s %-26s %.2f cm' % ('', 'L-R distance', '', span))
        print()
    return 0


if __name__ == '__main__':
    sys.exit(main())
