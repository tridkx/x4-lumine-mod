# -*- coding: utf-8 -*-
"""Assemble the Lumine X4 mod from the two exported packages.

    python tools/make_mod.py
    # then pack:  XRCatTool.exe -in work/x4_lumine_mod -out work/x4_lumine_mod/ext_01.cat

What this mod does
------------------
Replaces the **model** of every Terran-race female NPC with Lumine.  It does
*not* rewrite the appearance pools (which is what the earlier Argon-female mod
did): instead it replaces the `<models>` block of each of the 43 Terran-female
NPC macros named in `work/terran_female_macros.json`.

Two reasons that is the better shape:

* **The pools keep choosing different macros**, so an NPC's identity -- name,
  background, job title, the voice set -- stays varied.  Only the body changes.
  Rewriting the pool collapses every Terran woman into one macro.
* **Story and plot NPCs are covered.**  Macros like
  `character_terran_female_story_01_macro` or
  `character_scenario_combat_ter_captain_macro` are referenced directly by
  mission scripts and never appear in a pool.

Patching the shared base macro would be tidier, but it does not work here:
every derived Terran macro restates its own `<models>`, shadowing the base's.
(For Argon women the derived macros inherit, which is why the previous project
never hit this.)

The macro's other properties -- `identification`, `facemods`, `bonemods` -- are
left alone, so the face-shaping system still runs; it simply has no effect on a
head mesh that carries none of the blend bones.
"""

import json
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
WORK = os.path.join(PROJ, 'work')
PKG = os.path.join(WORK, "x4cc_pkg")
MOD = os.path.join(WORK, "x4_lumine_mod")
MOD_ID = "x4_lumine_mod"
ASSET_BASE = "extensions/%s/assets/characters/terran/lumine" % MOD_ID
DDS_DIR = os.path.join(WORK, 'tex_out', 'mats')

#: the macro list produced by tools/find_terran_female_macros.py
MACRO_LIST = os.path.join(WORK, 'terran_female_macros.json')

MACRO_NAME = 'character_terran_female_lumine_macro'

#: The extension is loaded after the DLCs (alphabetically `ego_*` < `x4_*`),
#: so its `<replace>` sees the final merged macro library.
MACRO_HEAD = ASSET_BASE + '/heads/lumine_head'
MACRO_BODY = ASSET_BASE + '/bodies/lumine_body'


def read(path):
    with open(path, encoding='utf-8') as fh:
        return fh.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(text)
    return path


def merge_assets():
    """Copy both packages' assets into the mod tree under one directory."""
    dst_root = os.path.join(MOD, 'assets', 'characters', 'terran', 'lumine')
    if os.path.exists(dst_root):
        shutil.rmtree(dst_root)
    os.makedirs(dst_root, exist_ok=True)

    xacs, textures = [], {}
    XAC_DEST = {'lumine_head.xac': 'heads', 'lumine_body.xac': 'bodies'}
    for pkg in ('lumine_head', 'lumine_body'):
        src = os.path.join(PKG, pkg, 'assets', 'characters', 'mycharacters')
        for root, _dirs, files in os.walk(src):
            for fn in files:
                sp = os.path.join(root, fn)
                if fn.endswith('.xac'):
                    sub = (XAC_DEST.get(fn)
                           or ('heads' if 'head' in fn.lower() else 'bodies'))
                    dp = os.path.join(dst_root, sub, fn)
                else:
                    dp = os.path.join(dst_root, 'textures', fn)
                os.makedirs(os.path.dirname(dp), exist_ok=True)
                shutil.copyfile(sp, dp)
                if fn.endswith('.xac'):
                    xacs.append(dp)
                else:
                    textures[fn] = dp
    return xacs, textures


def merge_material_library(textures):
    """Merge the two generated material libraries, then repair them.

    Two repairs, both because the converter's `build_material_library()` writes
    a fixed template rather than reading the Blender materials:

    * every texture path is the literal `PUT_YOUR_TEXTURE_PATH_HERE`;
    * **every material gets `shader="p1_character" blendmode="NONE"`**, no
      matter what `x4cc_shader` / `x4cc_blendmode` the material carries.  The
      previous project set `ALPHA1` on its stockings and shipped `NONE` -- its
      black stockings were never transparent in game.  So the shader and blend
      mode are taken from the manifest here, which is the only place they can
      come from.
    """
    manifest = json.load(open(os.path.join(DDS_DIR, 'manifest.json'),
                              encoding='utf-8'))
    collections = {}
    for pkg in ('lumine_head', 'lumine_body'):
        p = os.path.join(PKG, pkg, 'libraries', 'material_library.xml')
        if not os.path.exists(p):
            continue
        for m in re.finditer(r'<collection name="([^"]+)">(.*?)</collection>',
                             read(p), re.S):
            name, inner = m.group(1), m.group(2)
            block = collections.setdefault(name, {})
            for mm in re.finditer(r'<material name="([^"]+)".*?</material>',
                                  inner, re.S):
                block[mm.group(1)] = mm.group(0)

    if not collections:
        raise RuntimeError('no material collections found in the exported '
                           'packages -- did build_lumine_mod.py run?')

    def fix_path(match):
        return ('value="%s\\textures\\%s"'
                % (ASSET_BASE.replace('/', '\\'), match.group(1)))

    out = ["<?xml version='1.0' encoding='utf-8'?>", '<diff>',
           '  <add sel="/materiallibrary" pos="prepend">']
    total = 0
    unknown = []
    for coll, mats in sorted(collections.items()):
        out.append('    <collection name="%s">' % coll)
        for mname in sorted(mats):
            block = mats[mname]
            entry = manifest.get('%s.%s' % (coll, mname))
            if entry is None:
                unknown.append('%s.%s' % (coll, mname))
            else:
                block = re.sub(r'shader="[^"]*"',
                               'shader="%s"' % entry['shader'], block)
                block = re.sub(r'blendmode="[^"]*"',
                               'blendmode="%s"' % entry['blendmode'], block)
            block = re.sub(r'value="PUT_YOUR_TEXTURE_PATH_HERE\\([^"]+)"',
                           fix_path, block)
            out.append('      ' + block.strip())
            total += 1
        out.append('    </collection>')
    out += ['  </add>', '</diff>', '']
    if unknown:
        raise RuntimeError('no manifest entry for %s -- the shader and blend '
                           'mode would silently fall back to the converter '
                           'defaults' % unknown)
    write(os.path.join(MOD, 'libraries', 'material_library.xml'),
          '\n'.join(out))
    return total


def write_content():
    desc = ('Replaces every Terran female NPC model with Lumine from Genshin '
            'Impact.')
    cdesc = '所有泰伦（Terran）女性 NPC 的外观替换为《原神》的荧。'
    text = '''<?xml version="1.0" encoding="utf-8"?>
<content id="{id}" name="Lumine (Genshin Impact)" version="100" date="2026-09-24" save="0"
         description="{desc}">
  <text language="7"  name="Lumine (Genshin Impact)" description="{desc}"/>
  <text language="44" name="Lumine (Genshin Impact)" description="{desc}"/>
  <text language="86" name="荧 (原神)" description="{cdesc}"/>
</content>
'''.format(id=MOD_ID, desc=desc, cdesc=cdesc)
    return write(os.path.join(MOD, 'content.xml'), text)


def write_character_macros():
    """One <replace> per Terran-female macro, swapping its whole <models>."""
    if not os.path.exists(MACRO_LIST):
        raise RuntimeError('%s missing -- run tools/find_terran_female_macros.py'
                           % MACRO_LIST)
    macros = json.load(open(MACRO_LIST, encoding='utf-8'))

    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<diff>',
        '',
        '  <!-- Terran-female NPC macros: head/torso become Lumine, the random',
        '       hair props are switched off (her hair is baked into the head',
        '       asset, so a vanilla hairstyle would sit on top of it).',
        '       Only <models> is touched, so identification, facemods and',
        '       bonemods keep working as before.',
        '',
        '       These are patched one by one because each derived macro',
        '       restates <models>, shadowing the base macro it refs. -->',
        '',
    ]
    for name in macros:
        lines += [
            "  <replace sel=\"/macros/macro[@name='%s']/properties/models\">" % name,
            '    <models>',
            '      <model type="head"  ref="%s" />' % MACRO_HEAD,
            '      <model type="torso" ref="%s" />' % MACRO_BODY,
            '      <model type="props" ref="none" />',
            '      <model type="props2" ref="none" />',
            '    </models>',
            '  </replace>',
            '',
        ]
    # A convenience macro, so the model can also be spawned by name with
    # `add_npc` / the debug character test.  No pool selects it.  It lives in
    # this same file rather than its own: an extra `libraries/*.xml` is only
    # loaded if the game happens to scan the directory, and a missing entry
    # here fails silently (the macro simply does not exist).
    lines += [
        '  <!-- Not selected by any pool: a handle for spawning her directly. -->',
        '  <add sel="/macros">',
        '    <macro name="%s" class="npc"' % MACRO_NAME,
        '           ref="character_terran_female_cau_base_01_macro">',
        '      <component ref="character_argon_female_01" />',
        '      <properties>',
        '        <models>',
        '          <model type="head"  ref="%s" />' % MACRO_HEAD,
        '          <model type="torso" ref="%s" />' % MACRO_BODY,
        '          <model type="props"  ref="none" />',
        '          <model type="props2" ref="none" />',
        '        </models>',
        '      </properties>',
        '    </macro>',
        '  </add>',
        '',
        '</diff>',
        '',
    ]
    path = write(os.path.join(MOD, 'libraries', 'character_macros.xml'),
                 '\n'.join(lines))
    print('character_macros: %d macros patched (+1 spawnable macro)'
          % len(macros))
    return path


def main():
    if os.path.exists(MOD):
        shutil.rmtree(MOD)

    xacs, textures = merge_assets()
    print('assets copied : %d xac, %d textures' % (len(xacs), len(textures)))
    for x in sorted(xacs):
        print('   %s (%d KB)' % (os.path.relpath(x, MOD),
                                 os.path.getsize(x) // 1024))

    n = merge_material_library(textures)
    print('materials     : %d merged into one collection' % n)
    write_content()
    write_character_macros()
    print('xml written   : content.xml + macros')

    total = sum(os.path.getsize(os.path.join(r, f))
                for r, _d, fs in os.walk(MOD) for f in fs)
    print('mod size      : %.1f MB -> %s' % (total / 1e6, MOD))


if __name__ == '__main__':
    main()
