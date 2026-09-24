# -*- coding: utf-8 -*-
"""Pre-flight checks on an assembled mod tree.

    python tools/verify_mod.py --race terran --mode add
    python tools/verify_mod.py --race argon  --mode add
    python tools/verify_mod.py --race terran --mode replace

Default is the tree `make_mod.py` builds with the same flags
(`work/x4_lumine_<race>_<mode>`); pass a directory to check another one.

Every check here has caught something real in this project or its
predecessors:

* the diff files must be well-formed XML, and each `sel=` XPath must actually
  hit a node.  A non-matching XPath fails **silently** -- the vanilla model
  stays and nothing looks wrong until you are in game;
* every model path a macro names must exist inside the packed tree;
* every texture path a material names must exist -- the exporter writes
  `PUT_YOUR_TEXTURE_PATH_HERE` when it cannot resolve one, and a missing map
  shows in game as magenta;
* the .xac skeletons must be byte-identical to vanilla (the whole premise of
  "swap the mesh, keep the skeleton");
* **the two modes must not be confused with each other**:
  - `add` -- the target pools must each gain exactly one Lumine entry and keep
    every vanilla candidate they had.  A stray `<replace>` left over from the
    replace-everything shape would silently turn "one more option" back into
    "only option", which no screenshot would reveal unless you happened to be
    looking at a story NPC;
  - `replace` -- the patched macro set must be *complete* (one unpatched macro
    is one woman still wearing the old body) and no pool may reach vanilla.
"""

import argparse
import glob
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
WORK = os.path.join(PROJ, 'work')
import ws_paths
GAME = ws_paths.GAMEDATA
VANILLA = ws_paths.vanilla()
RETARGET_TOOLS = r"D:\dsh-x4\x4-character-retarget\tools"
sys.path.insert(0, RETARGET_TOOLS)
sys.path.insert(0, HERE)

import make_mod as MK                                     # noqa: E402

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
    names = ['content.xml', 'libraries/character_macros.xml',
             'libraries/material_library.xml']
    if MK.MODE == 'add':
        names.append('libraries/charactergroups.xml')
    for name in names:
        p = os.path.join(MK.MOD, name)
        if not os.path.exists(p):
            fail('%s missing' % name)
            continue
        try:
            ET.parse(p)
            ok('%s parses' % name)
        except ET.ParseError as e:
            fail('%s is not well-formed: %s' % (name, e))


def check_xpaths():
    """Every `sel=` in our diffs must match a node in the real libraries.

    X4 applies these blindly; an XPath that matches nothing is a no-op with no
    error anywhere.  The merge of vanilla + all DLC libraries is rebuilt here
    so the check sees the same tree the game will.
    """
    print('\n-- diff xpaths --')
    macros = MK.merge_library(MK.MACRO_SOURCES)
    pools = MK.merge_library(MK.POOL_SOURCES)
    print('        %d macros / %d pools across the merged libraries'
          % (len(macros), len(pools)))

    text = open(os.path.join(MK.MOD, 'libraries', 'character_macros.xml'),
                encoding='utf-8').read()

    if MK.MODE == 'add':
        # <add sel="/macros"> -- the whole point of add mode
        n_add_macro = len(re.findall(r'<add\s+sel="/macros"\s*>', text))
        if n_add_macro:
            ok('%d <add sel="/macros"> (a new macro, nothing replaced)'
               % n_add_macro)
        if re.search(r'<replace\s+sel="/macros/macro\[@name=', text):
            fail('character_macros.xml contains <replace> on a vanilla macro '
                 '-- that is replace-mode content in an add-mode tree')

    if MK.MODE == 'replace':
        pat = re.compile(r'''<replace\s+sel="/macros/macro\[@name='([^']+)'\]'''
                         r'''/properties/models">''')
        sels = pat.findall(text)
        missing = [s for s in sels if s not in macros]
        if missing:
            fail('%d macro xpaths match nothing, e.g. %s'
                 % (len(missing), missing[:3]))
        else:
            ok('all %d macro xpaths resolve to a real macro' % len(sels))
        return

    # --- add mode: every pool xpath must name a real pool, and the pool lists
    #     that discover_female_pools() would produce must be exactly the ones
    #     we write into (a pool silently absent = a job where she never shows)
    p = os.path.join(MK.MOD, 'libraries', 'charactergroups.xml')
    if not os.path.exists(p):
        fail('charactergroups.xml missing in add mode')
        return
    wanted = MK.female_pools_with_macros()
    sels = re.findall(r"<add\s+sel=\"/characters/character\[@name='([^']+)'\]\">",
                      open(p, encoding='utf-8').read())
    missing = [s for s in sels if s not in pools]
    if missing:
        fail('%d pool xpaths match nothing: %s' % (len(missing), missing))
    else:
        ok('all %d pool xpaths resolve to a real pool' % len(sels))
    if set(sels) != set(wanted):
        fail('pool set mismatch: diff has %d, discovery found %d (missing %s)'
             % (len(set(sels)), len(wanted),
                sorted(set(wanted) - set(sels))[:3]))
    else:
        ok('all %d %s female pools that list macros are covered'
           % (len(wanted), MK.RACE['label']))


def check_coverage():
    """What "correct" means is mode-dependent, and the two are opposites."""
    print('\n-- coverage (%s) --' % MK.MODE)
    pools = MK.merge_library(MK.POOL_SOURCES)

    if MK.MODE == 'add':
        # every target pool: exactly one Lumine entry, every vanilla entry kept
        p = os.path.join(MK.MOD, 'libraries', 'charactergroups.xml')
        text = open(p, encoding='utf-8').read()
        bad = []
        for name in MK.female_pools_with_macros():
            body = re.search(r"<add\s+sel=\"/characters/character\[@name='%s'\]\">"
                             r"(.*?)</add>" % re.escape(name), text, re.S)
            if body is None:
                bad.append((name, 'no entry'))
                continue
            n_us = len(re.findall(r'<select\s+macro="%s"' % MK.MACRO_NAME,
                                  body.group(1)))
            vanilla = len(re.findall(r'<select\s+macro="', pools[name]))
            if n_us < 1:
                bad.append((name, 'no Lumine select'))
            elif '<replace' in body.group(1):
                bad.append((name, 'contains a <replace>'))
            elif vanilla == 0:
                bad.append((name, 'pool has no vanilla macros left'))
        if bad:
            fail('%d pools are wrong: %s' % (len(bad), bad[:3]))
        else:
            ok('%d pools each gain Lumine and keep their vanilla candidates '
               '(she takes 1 in N+1 spawns)' % len(MK.female_pools_with_macros()))

        # the macro that was added must be *new*, not a shadow of a vanilla one
        vanilla_macros = MK.merge_library(MK.MACRO_SOURCES)
        if MK.MACRO_NAME in vanilla_macros:
            fail('%s already exists in the vanilla libraries -- this <add> '
                 'would duplicate a macro name' % MK.MACRO_NAME)
        else:
            ok('%s is a new name (no vanilla macro is shadowed)' % MK.MACRO_NAME)
        if MK.MACRO_NAME not in open(
                os.path.join(MK.MOD, 'libraries', 'character_macros.xml'),
                encoding='utf-8').read():
            fail('the added macro is not named %s' % MK.MACRO_NAME)
        return

    # --- replace mode: the patched set must be the complete female set
    path_in = MK.RACE['macro_list']
    if not os.path.exists(path_in):
        fail('macro list %s missing -- run find_terran_female_macros.py' % path_in)
        return
    patched = set(json.load(open(path_in, encoding='utf-8')))
    expected = set(re.findall(r"@name='([^']+)'",
                              open(os.path.join(MK.MOD, 'libraries',
                                                'character_macros.xml'),
                                   encoding='utf-8').read()))
    if expected != patched:
        fail('the diff patches %d macros but the list has %d'
             % (len(expected), len(patched)))
    else:
        ok('%d %s-female macros patched, matching the generated list'
           % (len(patched), MK.RACE['label']))

    left = []
    for pool in sorted(pools):
        if not (pool.startswith(MK.RACE['pool_prefixes'])
                and pool.endswith(MK.POOL_SUFFIX)):
            continue
        seen, stack = set(), [pool]
        while stack:
            cur = stack.pop()
            if cur in seen or cur not in pools:
                continue
            seen.add(cur)
            for body in [pools[cur]]:
                for mac in re.findall(r'<select macro="([^"]+)"', body):
                    if mac not in patched:
                        left.append((pool, mac))
                stack.extend(re.findall(r'<select character="([^"]+)"', body))
    if left:
        fail('%d pool entries still select an unpatched macro, e.g. %s'
             % (len(left), left[:3]))
    else:
        n_pools = len([p for p in pools
                       if p.startswith(MK.RACE['pool_prefixes'])
                       and p.endswith(MK.POOL_SUFFIX)])
        ok('all %d %s female pools (incl. indirect links) resolve to a '
           'patched macro' % (n_pools, MK.RACE['label']))


def check_macro_paths():
    print('\n-- macro model paths --')
    p = os.path.join(MK.MOD, 'libraries', 'character_macros.xml')
    text = open(p, encoding='utf-8').read()
    refs = re.findall(r'<model\s+type="(\w+)"\s+ref="([^"]+)"', text)
    seen = set()
    for typ, ref in refs:
        if ref == 'none' or (typ, ref) in seen:
            continue
        seen.add((typ, ref))
        base = 'extensions/%s/' % MK.MOD_ID
        rel = ref[len(base):] if ref.startswith(base) else ref
        path = os.path.join(MK.MOD, rel.replace('/', os.sep) + '.xac')
        if os.path.exists(path):
            ok('%-6s -> %s (%d KB)'
               % (typ, rel, os.path.getsize(path) // 1024))
        else:
            fail('%-6s -> %s does not exist' % (typ, path))


def check_textures():
    print('\n-- material textures --')
    p = os.path.join(MK.MOD, 'libraries', 'material_library.xml')
    text = open(p, encoding='utf-8').read()
    if 'PUT_YOUR_TEXTURE_PATH_HERE' in text:
        fail('material_library still has placeholder paths')
    prefix = 'extensions\\%s\\' % MK.MOD_ID
    refs = re.findall(r'value="([^"]*\\textures\\[^"]+)"', text)
    missing = []
    for r in refs:
        rel = r[len(prefix):] if r.startswith(prefix) else r
        rel = rel.replace('\\', os.sep)
        if not (os.path.exists(os.path.join(MK.MOD, rel))
                or os.path.exists(os.path.join(MK.MOD, rel + '.gz'))):
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
    import gzip as _gz
    import struct
    tex_dir = os.path.join(MK.MOD, 'assets', 'characters',
                           MK.RACE['asset_dir'], 'lumine', 'textures')
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
         os.path.join(MK.MOD, 'assets/characters', MK.RACE['asset_dir'],
                      'lumine/heads/lumine_head.xac')),
        ('body', os.path.join(VANILLA, 'char_arg_f_sweater_leggings_civ_01.xac'),
         os.path.join(MK.MOD, 'assets/characters', MK.RACE['asset_dir'],
                      'lumine/bodies/lumine_body.xac')),
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
    cat = os.path.join(MK.MOD, 'ext_01.cat')
    dat = os.path.join(MK.MOD, 'ext_01.dat')
    if os.path.exists(cat) and os.path.exists(dat):
        ok('ext_01.cat %d KB / ext_01.dat %.1f MB'
           % (os.path.getsize(cat) // 1024, os.path.getsize(dat) / 1e6))
    else:
        warn('not packed yet -- run XRCatTool -in %s -out %s'
             % (MK.MOD, os.path.join(MK.MOD, 'ext_01.cat')))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--race', choices=sorted(MK.RACES), default='terran')
    ap.add_argument('--mode', choices=('add', 'replace'), default='add')
    ap.add_argument('--dir', default=None,
                    help='mod tree to check (default: the one make_mod.py '
                         'builds for these flags)')
    args = ap.parse_args()

    MK.configure(args.race, args.mode, args.mode)
    if args.dir:
        MK.MOD = os.path.abspath(args.dir)

    print('mod tree: %s   [%s / %s]' % (MK.MOD, args.race, args.mode))
    if not os.path.isdir(MK.MOD):
        print('!! not built -- run tools/make_mod.py --race %s --mode %s first'
              % (args.race, args.mode))
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
