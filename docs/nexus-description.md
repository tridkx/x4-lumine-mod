# Nexus mod page content

**Mod name**: `Lumine (Genshin Impact) - Terran Female NPC Replacer`

**Summary / tagline** (one line for the mod card):
`Genshin Impact's Lumine joins (or replaces) the Terran female NPC models in X4: Foundations.`

**Three files, three shapes** -- pick one; the file name says which is which:
* `x4_lumine_terran_add_v1.2.zip` -- **add** (the normal build): Lumine joins the
  Terran and Pioneer female appearance pools as one more random candidate.
* `x4_lumine_terran_replace_v1.2.zip` -- **replace** (test build): every Terran
  woman becomes Lumine, story and mission NPCs included.
* `x4_lumine_argon_add_v1.2.zip` -- the same model for the **Argon** pools
  instead. Can be installed alongside the Terran one.

---

## Description (paste-ready, plain text)

```
Lumine (Genshin Impact) - Terran Female NPC Replacer

Brings Lumine from Genshin Impact into X4: Foundations as a Terran-race female
NPC model. Built the standard X4 way -- swap the meshes, keep the skeleton --
so it rides the vanilla shared rig and the full shared animation set and
modifies no game files.

There are three downloads of this mod. Pick one; do not install two that target
the same pools.


WHICH FILE DO I WANT?

  x4_lumine_terran_add_v1.2.zip    <- normal play, start here
    Lumine JOINS the Terran and Pioneer female appearance pools as one more
    random candidate: 12 pools (six each). Every vanilla model is left in
    place, so the other women keep their own faces, names and voices. She is
    about one in four of the women a pool spawns -- raise the number with
    --weight 2 if you want her about two in five.
    Story and mission NPCs never come from an appearance pool, so they keep
    their vanilla appearance.

  x4_lumine_terran_replace_v1.2.zip
    Lumine REPLACES all 45 Terran-race female NPC macros outright: every Terran
    and Pioneer woman you meet is her, story and mission NPCs included. This is
    the build for inspecting the model everywhere at once.

  x4_lumine_argon_add_v1.2.zip
    The same model, written into the Argon female pools (6 of them) instead of
    the Terran ones. Meshes, textures and materials are identical -- both races
    share the same body component -- so this file exists purely so Argon women
    can roll Lumine too. It can be installed together with the Terran build.
    Note: it competes for the same pools as the other Argon appearance mods
    (Rose, Emilie, ...), so whichever loads last is what you see.


VERSION
  1.2 (all three)

GAME VERSION
  X4: Foundations 9.00 (built and tested on 9.00)
  The Terran builds require the Cradle of Humanity DLC -- that is where the
  Terran race is. The Argon build does not.


INSTALLATION

  1. Download the zip you want.

  2. Unpack it into the game's extensions folder, so you end up with:

       X4 Foundations\extensions\x4_lumine_mod\
           content.xml
           ext_01.cat
           ext_01.dat

  3. Start the game, open the Extensions menu from the main menu, and enable
     "Lumine (Genshin Impact)".

  4. Load a save or start a new one and look at a Terran or Pioneer woman.
     Terran space (Segaris, Mars, the Moon, Getsu Fune) and Pioneer stations
     are the places to go. With the Argon build, any station with Argon women
     will do.

  Note: an NPC's appearance is decided when it is created, so NPCs already
  standing in front of you will not change. Move to an area with the right
  women, or reload, and they will.

  The builds write the same file names, so switching means replacing the folder
  contents -- not merging them.


UNINSTALLATION

  Delete the extensions\x4_lumine_mod folder, or just untick it in the
  Extensions menu. Nothing in the game is modified, so saves stay valid either
  way.


WHAT EXACTLY GETS CHANGED

  ADD build (the default shape)

    One new NPC macro is appended -- it inherits the vanilla base macro, so her
    race/gender identification, eye positions and face-shaping all still run --
    and one line is added to each of the 12 Terran and Pioneer female
    appearance pools:

      civilian, manager, marine, pilot, service, factiondiplomat
      (six for the Terran faction, six for the Pioneers)

    With the Argon build it is the same macro pointed at the Argon base, and
    the six Argon female pools:

      civilian, commander, marine, pilot, service, factiondiplomat

    Not a single vanilla macro and not a single existing pool entry is removed.
    The pool lists are read from the game itself, so a pool added by a DLC is
    picked up rather than missed.

  REPLACE build

    All 45 Terran-race female NPC macros have their head and torso models
    re-pointed at Lumine. That set is defined by data, not by names: for every
    candidate macro the project resolves race / gender / faction through its
    inheritance chain, and also includes every macro reachable from the Terran
    and Pioneer female pools -- which is how the story and mission characters
    that never appear in a pool end up covered.

    Their identities are untouched: names, job titles, backgrounds and voice
    sets still vary normally. Only the body changes.

  NOT changed by any build: Yaki women, and the player's own character.


KNOWN ISSUES AND LIMITATIONS

  Please read these before installing.

  1. Joints tear under the skin at the ankles, shoulders and elbows
     This is the one visible flaw, and it is the honest reason to read this
     section. At the ankle you will see the boot collar sit slightly off the
     leg; at the shoulder and elbow there is a small gap.

     Cause: this model's rig stacks its spine bones on top of each other --
     下半身 and 上半身 are 0.7 cm apart -- while X4's Bip01 Spine and Spine1 are
     12.8 cm apart. Matching each bone to its X4 counterpart therefore pulls
     two vertex sets that are almost coincident in the source 12.8 cm apart,
     and the skinning blends them, so every edge spanning them stretches.
     Measured: 394 edges stretch past 2x their source length.

     I tried the obvious fix -- giving each bone chain one shared translation
     offset, the same trick that already fixes the neck and the feet. It
     reduces the numbers but introduces visible BENDING at the arms and
     ankles, which looks worse than the seam it removes, so it was reverted.
     Weight smoothing does not help either: 4, 10, 20 and 40 passes give
     identical results.

     Fixing it properly would mean changing bone proportions, and the skeleton
     has to stay byte-identical to vanilla or the animations break. So it
     stays. It is most visible in close-ups and still visible at normal
     conversation distance.

  2. Fingers do not move individually
     They are bound to the palm. That is the price of a correct hand shape:
     the source models the fingers together while the X4 skeleton splays them,
     and matching each finger to its own bone tears the web between thumb and
     index open until it looks like a piece of skin is missing.

  3. Hair and ornaments are rigid
     Bound to the head bone as one piece, so they turn with the head and do
     not sway. The 91-bone X4 rig has no hair chain to bind to.

  4. Skirt and ribbons have no cloth motion
     Same reason -- the whole chain is anchored to the spine. They hold their
     shape and follow the body, but they do not swing when walking.

  5. The eyes do not track
     They are fixed to the head rather than driven by X4's look-at system.
     X4 moves the eyeballs with dedicated dummy bones, and this model's eye
     geometry sits far enough from them that a gaze change would swing the
     eyeballs out of the sockets.

  6. No facial expression or lip sync
     X4's procedural face system (facemods) and voice lip sync do not apply.
     Lumine has a fixed face.

  7. Fine dark lines on the clothing are exaggerated up close
     Decoration edges on this model are geometry mapped to a very narrow strip
     of the texture atlas (one measured face spans 56 x 2 texels), so the
     renderer magnifies two texels into a visible band. It reads as trim at
     normal distance and as stripes in a close-up. It is in the source art.

  8. No normal maps, and roughness is a constant per material
     The source is an MMD model: diffuse maps only, no normal/roughness/
     metallic channels. Flat BC5 normal maps are generated as placeholders and
     roughness is set per material by hand.

  9. Coarser than the source model
     X4 renders NPCs instanced, so an asset has to stay near vanilla's ~5k
     vertices. This one ships at 4813 (head) and 11325 (body) against vanilla's
     4693 and 3601 -- about 1.03x and 3.15x. That is comfortably inside budget,
     and it is why the model is not decimated further (decimation rewrites UVs,
     and these atlases are shared per material, so a shifted UV samples a
     neighbouring part of the sheet).


COMPATIBILITY

  - Requires X4: Foundations 9.00 or newer. The Terran builds also require the
    Cradle of Humanity DLC; the Argon build does not.
  - Modifies no game files; coexists with most mods.
  - The Terran ADD build sits alongside the Argon appearance replacers (Rose,
    Emilie, 2B, ...): those edit the Argon pools, this one appends to the Terran
    and Pioneer pools. It also sits alongside other Terran appearance replacers
    -- they share the pools, so each one's share of the spawns drops.
  - The Terran REPLACE build conflicts with other Terran appearance replacers:
    both would be replacing the same 45 macros and the last one loaded wins.
  - The ARGON build competes for the same six Argon pools as the other Argon
    appearance replacers -- whichever loads last is what you see. That is the
    only sense in which the Argon build "conflicts" with them.
  - Save safe: enable or disable at any time.


REQUIREMENTS

  A legitimate copy of X4: Foundations. The two Terran builds also require the
  Cradle of Humanity DLC (that is where the Terran race comes from); the Argon
  build is usable without it. These mods contain only converted assets, no game
  files.


AI USAGE

  The tooling behind this mod -- the PMX parser, the retargeting algorithm,
  the texture and packaging pipeline, and the diagnostic scripts -- was written
  with the help of an AI assistant. The design decisions, the in-game testing
  and the diagnosis of every issue were done by the author.

  The project keeps a full engineering log documenting every bug found and
  fixed, and it is unusually candid about the ones that were not: the joint
  tearing in issue 1 is recorded there as an open problem along with the fix
  that was attempted and reverted.

  The model and textures are converted from the source model; they are not
  AI-generated.


CREDITS

  - X4 Character Converter by DiCrash / Orion -- without this exporter none of
    this would exist
    https://www.nexusmods.com/x4foundations/mods/2152
  - EGOSOFT's X Tools and the X4 modding documentation

  (These are the tools used to build this mod.  Players do not need to install
  any of them.)


LEGAL

  Genshin Impact is a trademark of miHoYo / HoYoverse. X4: Foundations is a
  trademark of EGOSOFT. This is an unofficial fan work for personal use and
  contains no game assets from either title. The Lumine model and textures
  remain the property of miHoYo; the model conversion is by 观海
  (Bilibili: 观海子) and is itself a derivative work.
```
