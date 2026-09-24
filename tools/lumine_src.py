# -*- coding: utf-8 -*-
"""Where the source model lives and what its Japanese material names mean.

Kept in one place so every diagnostic and both build stages agree; the previous
project lost a round to a diagnostic that used its own copy of this table and
silently disagreed with the builder.
"""

import os

SRC_DIR = (r"C:\Users\DKX\Desktop\新建文件夹 (3)"
           r"\【女主角_荧】_by_原神_39fd8673fd145a6c65858227788cb173")
SRC_PMX = os.path.join(SRC_DIR, "荧.pmx")

#: The converter only accepts `[a-z0-9_]` for object names and
#: `[a-z0-9_]+\.[a-z0-9_]+` for materials, so every Chinese material name has
#: to become an ascii stem before it reaches the addon.
#:
#: Note `髪` (U+9AEA) here against the previous project's `髮` (U+9AEE): the two
#: look alike and are different code points, so this table cannot be copied
#: between models -- it has to be generated from the actual material list.
MAT_ASCII = {
    '颜': 'face',          # face skin
    '颜2': 'face2',        # face shading overlay
    '白目': 'eyewhite',    # sclera
    '眉': 'brow',
    '二重': 'eyelid',      # double eyelid line
    '睫': 'eyelash',
    '口': 'mouth',
    '齿': 'teeth',
    '星目': 'eyespec',     # eye highlight
    '髪': 'hair',
    '目': 'iris',          # iris / pupil
    '头饰': 'acc1',        # hair ornament
    '花蕊': 'acc2',        # flower centre
    '衣': 'cloth',
    '飘带': 'ribbon',
    '裙': 'skirt',
    '南瓜裤': 'petti',     # bloomers / petticoat
    '肌': 'skin',
    '元素+': 'elem',       # elemental glow
    '髪+': 'hairspec',     # hair specular overlay (coincident with 髪)
}


def stem_of(name):
    return MAT_ASCII.get(name)


#: Materials that are dropped before anything is built, because they are
#: coincident overlays on a base layer and would z-fight in the engine's depth
#: buffer.  Measured in `diag_overlays.py`:
#:
#:     hairspec (髪+, sp.png)  1682 verts, 100% within 1 mm of `hair`
#:                             (median 0.00 mm), and 98% of it is transparent
#:     elem     (元素+, 元素1)  229 verts, 100% within 1 mm of `cloth`
#:
#: `hairspec` is dropped outright -- a 98%-transparent specular overlay that
#: adds nothing but a second shell at the same depth.  `elem` is *kept*, since
#: it is a visible crest on the chest, and pushed off the surface instead (see
#: ELEM_OFFSET in build_lumine_x4).
#:
#: Defined here rather than in the builder so the texture step and the build
#: step cannot disagree about what exists -- a mismatch would either ship an
#: unused 5 MB atlas or reference a DDS that was never written.
DROP_STEMS = {'hairspec'}
