# -*- coding: utf-8 -*-
"""Pre-flight checks on the assembled mod tree.

    python tools/verify_mod.py

Every check here has caught something real in this project or its
predecessors:

* the diff files must be well-formed XML, and each `<replace>` XPath must
  actually hit a node.  A non-matching XPath fails **silently** -- the vanilla
  model stays and nothing looks wrong until you are in game;
* every model path a macro names must exist inside the packed tree;
* every texture path a material names must exist -- the exporter writes
  `PUT_YOUR_TEXTURE_PATH_HERE` when it cannot resolve one, and a missing map
  shows in game as magenta;
* the .xac skeletons must be byte-identical to vanilla (the whole premise of
  "swap the mesh, keep the skeleton");
* the 43 patched macros must be the *complete* set of Terran-female macros, and
  no appearance pool may still reach a vanilla Terran face.  A missing macro
  means one woman in the game still has the old body, which is exactly the
  kind of thing that is invisible in a screenshot.
"""

import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
WORK = os.path.join(PROJ, 'work')
MOD = os.path.join(WORK, 'x4_lumine_mod')
VANILLA = os.path.join(r"D:\dsh-x4\work", 'vanilla')
DLC = os.path.join(r"D:\dsh-x4\work", 'dlc_terran')
RETARGET_TOOLS = r"D:\dsh-x4\x4-character-retarget\tools"
sys.path.insert(0, RETARGET_TOOLS)
sys.path.insert(0, HERE)

FAIL = []
WARN = []


def ok(msg):
    print('  ok    %s' % msg)


def fail(msg):
    print('  FAIL  %s' % msg)
    FAIL.append(msg)


def warn(msg):
    print('  warn  %s' % msg)
    WARN.append(msg)


def check_xml():
    print('\n-- xml --')
    for name in ('content.xml', 'libraries/character_macros.xml',
                 'libraries/material_library.xml'):
        p = os.path.join(MOD, name)
        if not os.path.exists(p):
            fail('%s missing' % name)
            continue
        try:
            ET.parse(p)
            ok('%s parses' % name)
        except ET.ParseError as e:
            fail('%s is not well-formed: %s' % (name, e))


def check_xpaths():
    """Every <replace sel=...> must resolve against the real macro library.

    X4 applies these blindly; an XPath that matches nothing is a no-op with no
    error anywhere.  The merge of vanilla + all seven DLC libraries is rebuilt
    here so the check sees the same tree the game will.
    """
    print('\n-- diff xpaths --')
    import glob
    sources = [os.path.join(VANILLA, 'libraries', 'character_macros.xml')]
    sources += sorted(glob.glob(
        os.path.join(r"D:\dsh-x4\work", 'dlc_all', '*',
                     'libraries', 'character_macros.xml')))
    names = set()
    for p in sources:
        if os.path.exists(p):
            names.update(re.findall(r'<macro\s+name="([^"]+)"',
                                    open(p, encoding='utf-8').read()))
    print('        %d macro names across %d libraries'
          % (len(names), len([p for p in sources if os.path.exists(p)])))

    p = os.path.join(MOD, 'libraries', 'character_macros.xml')
    pat = re.compile(r'''<replace\s+sel="/macros/macro\[@name='([^']+)'\]'''
                     r'''/properties/models">''')
    sels = pat.findall(open(p, encoding='utf-8').read())
    missing = [s for s in sels if s not in names]
    if missing:
        fail('%d macro xpaths match nothing, e.g. %s'
             % (len(missing), missing[:3]))
    else:
        ok('all %d macro xpaths resolve to a real macro' % len(sels))


def check_coverage():
    """The patched set must cover every Terran-female macro that exists."""
    print('\n-- coverage --')
    if not os.path.exists(MACRO_LIST_PATH):
        fail('macro list missing -- run find_terran_female_macros.py')
        return
    patched = set(json.load(open(MACRO_LIST_PATH, encoding='utf-8')))
    expected = re.findall(r"@name='([^']+)'",
                          open(os.path.join(MOD, 'libraries',
                                            'character_macros.xml'),
                               encoding='utf-8').read())
    if set(expected) != patched:
        fail('the diff patches %d macros but the list has %d'
             % (len(set(expected)), len(patched)))
    else:
        ok('%d Terran-female macros patched, matching the generated list'
           % len(patched))

    # Every pool that can spawn a Terran woman must reach a patched macro.
    # Pools may point at other pools, so those links are walked too -- the
    # first version of this check only looked at direct <select macro=> and
    # missed the two diplomat entries entirely.
    import find_terran_female_macros as F
    pools = F.load_pools()
    left = []
    for pool in sorted(pools):
        if not (pool.startswith(('terran.', 'pioneers.'))
                and pool.endswith('.female')):
            continue
        seen, stack = set(), [pool]
        while stack:
            cur = stack.pop()
            if cur in seen or cur not in pools:
                continue
            seen.add(cur)
            for body in pools[cur]:
                for mac in re.findall(r'<select macro="([^"]+)"', body):
                    if mac not in patched:
                        left.append((pool, mac))
                stack.extend(re.findall(r'<select character="([^"]+)"', body))
    if left:
        fail('%d pool entries still select an unpatched macro, e.g. %s'
             % (len(left), left[:3]))
    else:
        n_pools = len([p for p in pools
                       if p.startswith(('terran.', 'pioneers.'))
                       and p.endswith('.female')])
        ok('all %d terran.*/pioneers.* female pools (incl. indirect links) '
           'resolve to a patched macro' % n_pools)


def check_macro_paths():
    print('\n-- macro model paths --')
    for fn in ('character_macros.xml',):
        p = os.path.join(MOD, 'libraries', fn)
        if not os.path.exists(p):
            continue
        text = open(p, encoding='utf-8').read()
        refs = re.findall(r'<model\s+type="(\w+)"\s+ref="([^"]+)"', text)
        seen = set()
        for typ, ref in refs:
            if ref == 'none' or (typ, ref) in seen:
                continue
            seen.add((typ, ref))
            base = 'extensions/x4_lumine_mod/'
            rel = ref[len(base):] if ref.startswith(base) else ref
            path = os.path.join(MOD, rel.replace('/', os.sep) + '.xac')
            if os.path.exists(path):
                ok('%-6s -> %s (%d KB)'
                   % (typ, rel, os.path.getsize(path) // 1024))
            else:
                fail('%-6s -> %s does not exist' % (typ, path))


def check_textures():
    print('\n-- material textures --')
    p = os.path.join(MOD, 'libraries', 'material_library.xml')
    text = open(p, encoding='utf-8').read()
    if 'PUT_YOUR_TEXTURE_PATH_HERE' in text:
        fail('material_library still has placeholder paths')
    prefix = 'extensions\\x4_lumine_mod\\'
    refs = re.findall(r'value="([^"]*\\textures\\[^"]+)"', text)
    missing = []
    for r in refs:
        rel = r[len(prefix):] if r.startswith(prefix) else r
        rel = rel.replace('\\', os.sep)
        if not (os.path.exists(os.path.join(MOD, rel))
                or os.path.exists(os.path.join(MOD, rel + '.gz'))):
            missing.append(r)
    if missing:
        fail('%d texture refs have no file, e.g. %s' % (len(missing), missing[0]))
    else:
        ok('%d texture references all resolve' % len(refs))
    mats = re.findall(r'<material name="([^"]+)"', text)
    blend = re.findall(r'<material name="([^"]+)"[^>]*blendmode="([^"]+)"', text)
    nz = [b for b in blend if b[1] != 'NONE']
    print('        %d materials (%d with a blend mode: %s)'
          % (len(mats), len(nz), ', '.join('%s=%s' % b for b in nz)))
    if 'diffuse_map" value="' in text and 'magenta' in text:
        warn('unexpected magenta reference')


def check_mipmaps():
    """Every shipped DDS must carry a full mip chain.

    A level-0-only texture is not a cosmetic detail: the character atlases are
    dense strand/weave patterns, and without mips the GPU point-samples them,
    so at any distance golden hair aliases into crawling black stripes and
    white cloth into grey ones.  Every vanilla character texture checked ships
    a full chain (2048^2 -> mipCount=12), so this asserts parity rather than
    a preference.
    """
    print('\n-- texture mip chains --')
    import glob
    import gzip as _gz
    import struct
    tex_dir = os.path.join(MOD, 'assets', 'characters', 'terran', 'lumine',
                           'textures')
    files = sorted(glob.glob(os.path.join(tex_dir, '*.gz')))
    if not files:
        fail('no textures in %s' % tex_dir)
        return
    bad = []
    for f in files:
        raw = _gz.decompress(open(f, 'rb').read())
        if raw[:4] != b'DDS ':
            bad.append((os.path.basename(f), 'not DDS'))
            continue
        # legacy DDS header layout: 8 dwFlags, 12 dwHeight, 16 dwWidth,
        # 28 dwMipMapCount.  Reading width from 16 and height from 20 (i.e.
        # the pitch field) makes a 1024x1024 texture look like 1024x2048 and
        # then demands one mip level too many.
        h = struct.unpack('<I', raw[12:16])[0]
        w = struct.unpack('<I', raw[16:20])[0]
        mips = struct.unpack('<I', raw[28:32])[0]
        flags = struct.unpack('<I', raw[8:12])[0]
        expect = 1
        while max(w, h) >> expect >= 1:
            expect += 1
        if mips != expect or not (flags & 0x20000):
            bad.append((os.path.basename(f), '%dx%d mips=%d expected %d'
                        % (w, h, mips, expect)))
    if bad:
        fail('%d textures without a full mip chain, e.g. %s'
             % (len(bad), bad[:3]))
    else:
        ok('all %d textures carry a full mip chain' % len(files))


def check_skeletons():
    print('\n-- skeletons --')
    import xac
    pairs = [
        ('head', os.path.join(VANILLA, 'char_arg_f_dyn_blend_head.xac'),
         os.path.join(MOD, 'assets/characters/terran/lumine/heads/lumine_head.xac')),
        ('body', os.path.join(VANILLA, 'char_arg_f_sweater_leggings_civ_01.xac'),
         os.path.join(MOD, 'assets/characters/terran/lumine/bodies/lumine_body.xac')),
    ]
    for tag, van, mod in pairs:
        if not (os.path.exists(van) and os.path.exists(mod)):
            warn('%s: cannot compare (missing file)' % tag)
            continue
        print('        --- %s ---' % tag)
        r = xac.compare_skeletons(van, mod, verbose=True)
        if r is False:
            fail('%s: skeleton does not match vanilla' % tag)


def check_catalog():
    print('\n-- catalog --')
    cat = os.path.join(MOD, 'ext_01.cat')
    dat = os.path.join(MOD, 'ext_01.dat')
    if os.path.exists(cat) and os.path.exists(dat):
        ok('ext_01.cat %d KB / ext_01.dat %.1f MB'
           % (os.path.getsize(cat) // 1024, os.path.getsize(dat) / 1e6))
    else:
        warn('not packed yet -- run XRCatTool -in %s -out %s'
             % (MOD, os.path.join(MOD, 'ext_01.cat')))


MACRO_LIST_PATH = os.path.join(WORK, 'terran_female_macros.json')


def main():
    print('mod tree: %s' % MOD)
    if not os.path.isdir(MOD):
        print('!! not built -- run tools/make_mod.py first')
        return 1
    check_xml()
    check_xpaths()
    check_coverage()
    check_macro_paths()
    check_textures()
    check_mipmaps()
    check_skeletons()
    check_catalog()

    print('\n' + '=' * 70)
    if FAIL:
        print('RESULT: %d failure(s), %d warning(s)' % (len(FAIL), len(WARN)))
        for f in FAIL:
            print('   - %s' % f)
        return 1
    print('RESULT: all checks passed (%d warnings)' % len(WARN))
    return 0


if __name__ == '__main__':
    sys.exit(main())
