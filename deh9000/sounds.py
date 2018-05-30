"""Constants and types for Doom's sound effects table.

The S_sfx array lists the different sound effects which play within the game.
In the Doom source code the equivalent definitions are found in sounds.h.
"""

from __future__ import absolute_import

from deh9000 import c

class sfxinfo_t(c.Struct):
	"""Struct type representing the sound effects played in game.

	Each sound effect that can be played has an entry in the S_sfx table.
	In Dehacked these are the "Sound" sections.
	"""
	DEHACKED_NAME = "Sound"

	name        = c.StructField(None)  # "Offset"
	singularity = c.StructField("Zero/One")
	priority    = c.StructField("Value")
	link        = c.StructField(None)  # "Zero 1"
	pitch       = c.StructField("Zero 2")
	volume      = c.StructField("Zero 3")
	data        = c.StructField("Zero 4")
	usefulness  = c.StructField("Neg. One 1")
	lumpnum     = c.StructField("Neg. One 2")


sfxenum_t = c.Enum([
	"sfx_None",
	"sfx_pistol",
	"sfx_shotgn",
	"sfx_sgcock",
	"sfx_dshtgn",
	"sfx_dbopn",
	"sfx_dbcls",
	"sfx_dbload",
	"sfx_plasma",
	"sfx_bfg",
	"sfx_sawup",
	"sfx_sawidl",
	"sfx_sawful",
	"sfx_sawhit",
	"sfx_rlaunc",
	"sfx_rxplod",
	"sfx_firsht",
	"sfx_firxpl",
	"sfx_pstart",
	"sfx_pstop",
	"sfx_doropn",
	"sfx_dorcls",
	"sfx_stnmov",
	"sfx_swtchn",
	"sfx_swtchx",
	"sfx_plpain",
	"sfx_dmpain",
	"sfx_popain",
	"sfx_vipain",
	"sfx_mnpain",
	"sfx_pepain",
	"sfx_slop",
	"sfx_itemup",
	"sfx_wpnup",
	"sfx_oof",
	"sfx_telept",
	"sfx_posit1",
	"sfx_posit2",
	"sfx_posit3",
	"sfx_bgsit1",
	"sfx_bgsit2",
	"sfx_sgtsit",
	"sfx_cacsit",
	"sfx_brssit",
	"sfx_cybsit",
	"sfx_spisit",
	"sfx_bspsit",
	"sfx_kntsit",
	"sfx_vilsit",
	"sfx_mansit",
	"sfx_pesit",
	"sfx_sklatk",
	"sfx_sgtatk",
	"sfx_skepch",
	"sfx_vilatk",
	"sfx_claw",
	"sfx_skeswg",
	"sfx_pldeth",
	"sfx_pdiehi",
	"sfx_podth1",
	"sfx_podth2",
	"sfx_podth3",
	"sfx_bgdth1",
	"sfx_bgdth2",
	"sfx_sgtdth",
	"sfx_cacdth",
	"sfx_skldth",
	"sfx_brsdth",
	"sfx_cybdth",
	"sfx_spidth",
	"sfx_bspdth",
	"sfx_vildth",
	"sfx_kntdth",
	"sfx_pedth",
	"sfx_skedth",
	"sfx_posact",
	"sfx_bgact",
	"sfx_dmact",
	"sfx_bspact",
	"sfx_bspwlk",
	"sfx_vilact",
	"sfx_noway",
	"sfx_barexp",
	"sfx_punch",
	"sfx_hoof",
	"sfx_metal",
	"sfx_chgun",
	"sfx_tink",
	"sfx_bdopn",
	"sfx_bdcls",
	"sfx_itmbk",
	"sfx_flame",
	"sfx_flamst",
	"sfx_getpow",
	"sfx_bospit",
	"sfx_boscub",
	"sfx_bossit",
	"sfx_bospn",
	"sfx_bosdth",
	"sfx_manatk",
	"sfx_mandth",
	"sfx_sssit",
	"sfx_ssdth",
	"sfx_keenpn",
	"sfx_keendt",
	"sfx_skeact",
	"sfx_skesit",
	"sfx_skeatk",
	"sfx_radio",
])

sfxenum_t.create_globals(globals())

# To match the Doom source, but if you're really a Python programmer you
# probably shouldn't be using this.
NUMSFX = len(sfxenum_t)

