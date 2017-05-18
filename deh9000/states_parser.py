"""Parser for DECORATE-style States {} definitions.

The DECORATE syntax for defining states makes for a very clean way of defining
actor states and animations. In particular it's probably convenient for
converting such animations from DECORATE format to Dehacked.
"""

import actions
from sprites import spritenum_t
from states import state_t
import re

# eg. "Spawn:"
GOTO_LABEL_RE = re.compile(r"\s*(?P<label>\w+)\s*:\s*")

# Examples:
# BSPI A 20
# BSPI A 3 A_BabyMetal
# BOSF A 3 BRIGHT A_SpawnSound
# APLS AB 5 BRIGHT
# BOSF BCD 3 BRIGHT A_SpawnFly

FRAME_DEF_RE = re.compile(r"\s*(?P<sprname>\w\w\w\w)"
                          r"\s+(?P<frame>[a-z]+)"
                          r"\s+(?P<tics>\-?\d+)"
                          r"\s*(?P<bright>bright)?"
                          r"\s*(?P<action>A_\w+)?"
                          r"\s*$", re.I)

# Examples:
# Goto See
# Goto Spawn+1
GOTO_STATEMENT_RE = re.compile(r"\s*Goto"
                               r"\s+(?P<label>\w+)"
                               r"\s*(\+\s*(?P<offset>\d+))?"
                               r"\s*$", re.I)

# Jump back to last labeled state:
LOOP_STATEMENT_RE = re.compile(r"\s*Loop\s*$")

# End of sequence
STOP_STATEMENT_RE = re.compile(r"\s*Stop\s*$")

# What the *state fields are called in DECORATE:
DECORATE_NAMES = {
	# mobj_t fields:
	"see":     "seestate",
	"spawn":   "spawnstate",
	"pain":    "painstate",
	"melee":   "meleestate",
	"missile": "missilestate",
	"death":   "deathstate",
	"xdeath":  "xdeathstate",
	"raise":   "raisestate",

	# weaponinfo_t fields:
	"select":   "upstate",
	"deselect": "downstate",
	"ready":    "readystate",
	"fire":     "atkstate",
	"flash":    "flashstate",
}

class StatesParseException(Exception):
	pass

class StateRemapException(Exception):
	pass

def sprite_for_name(name):
	try:
		return spritenum_t.index("SPR_" + name.upper())
	except ValueError:
		raise StatesParseException("Unknown sprite %r" % name)


def action_pointer_for_name(name):
	if not name:
		return None
	if (not hasattr(actions, name) or
	    not isinstance(getattr(actions, name), actions.Action)):
		raise StatesParseException("Unknown action pointer %r" % name)
	return getattr(actions, name)


def construct_states(params):
	sprite_num = sprite_for_name(params["sprname"])
	tics = int(params["tics"])
	is_bright = params.get("bright") != None
	action = action_pointer_for_name(params.get("action"))

	for fr in params["frame"]:
		frame = ord(fr.lower()) - ord('a')
		if is_bright:
			frame |= 32768
		yield state_t(
			sprite=sprite_num,
			frame=frame,
			tics=tics,
			action=action,
		)


class _Parser(object):
	def __init__(self):
		self.states = [state_t()]
		self.state_labels = {}
		self.previous_state_id = -1
		self.loop_start_id = -1
		self.saved_gotos = []

	def more_lines(self):
		while self.lines and self.lines[0].strip() == "":
			self.line_number += 1
			self.lines.pop(0)
		return len(self.lines) > 0

	def next_line(self):
		if not self.more_lines():
			return ""
		#print "next line: %r" % self.lines[0]
		return self.lines[0]

	def matches_regexp(self, regexp):
		line = self.next_line()
		m = regexp.match(line)
		if m:
			#print "%r matches %r" % (line, regexp)
			self.lines[0] = line[m.end():]
			return m

	def parse_labels(self):
		labels = set()
		while True:
			m = self.matches_regexp(GOTO_LABEL_RE)
			if not m:
				break
			labels.add(m.groupdict()["label"])
		return labels

	def exception(self, s, line_number=None):
		if line_number is None:
			line_number = self.line_number
		raise StatesParseException("line %d: %s" % (line_number, s))

	def set_label(self, name, state_id):
		if name in self.state_labels:
			self.exception("Label %r defined multiple times." % (
				name))
		self.state_labels[name] = state_id
		# We also set loop_start_id so we know which is the last
		# label defined before a loop statement.
		self.loop_start_id = state_id

		# Also see if there's a Doom equivalent name:
		doom_name = DECORATE_NAMES.get(name.lower())
		if doom_name and doom_name not in self.state_labels:
			self.state_labels[doom_name] = state_id

	def alloc_new_state(self):
		result = len(self.states)
		self.states.append(state_t())
		return result

	def parse_frame_def(self):
		labels = self.parse_labels()
		m = self.matches_regexp(FRAME_DEF_RE)
		if not m:
			return False
		for state in construct_states(m.groupdict()):
			state_id = self.alloc_new_state()
			self.states[state_id].copy_from(state)

			# Link in states in a chain:
			if self.previous_state_id != -1:
				previous_state = (
					self.states[self.previous_state_id])
				previous_state.nextstate = state_id
			self.previous_state_id = state_id

			# If there were labels for this sequence, they should
			# be stored and pointed to the first stated in seq:
			for label in labels:
				self.set_label(label, state_id)
			labels = set()
		return True

	def parse_loop(self):
		if not self.matches_regexp(LOOP_STATEMENT_RE):
			return False

		if self.previous_state_id == -1:
			self.exception("Loop without a preceding state")
		if self.loop_start_id == -1:
			self.exception("Loop without a preceding label")
		state = self.states[self.previous_state_id]
		state.nextstate = self.loop_start_id
		self.previous_state_id = -1
		self.loop_start_id = -1
		return True

	def parse_stop(self):
		if not self.matches_regexp(STOP_STATEMENT_RE):
			return False

		if self.previous_state_id == -1:
			self.exception("Stop without a preceding state")
		state = self.states[self.previous_state_id]
		state.tics = -1
		state.nextstate = 0
		self.previous_state_id = -1
		self.loop_start_id = -1
		return True

	def parse_goto(self):
		m = self.matches_regexp(GOTO_STATEMENT_RE)
		if not m:
			return False
		if self.previous_state_id == -1:
			self.exception("Goto without a previous state")
		# We can't "apply" this goto statement yet since it may refer
		# to a label that we haven't parsed yet. So we save it for
		# later.
		params = m.groupdict()
		self.saved_gotos.append((
			self.line_number,
			self.previous_state_id,
			params["label"],
			int(params.get("offset") or "0"),
		))
		self.previous_state_id = -1
		self.loop_start_id = -1
		return True

	def resolve_goto(self, line_number, label, offset):
		if label not in self.state_labels:
			self.exception("Goto to unknown label %r" % (label),
			               line_number=line_number)

		state_id = self.state_labels[label]
		for _ in range(offset):
			next_state_id = self.states[state_id].nextstate
			if next_state_id == -1:
				self.exception(
					"Goto offset %r + %d is longer than "
					"animation sequence" % (
						label, offset),
					line_number=line_number)
			state_id = next_state_id
		return state_id

	def apply_gotos(self):
		for line_number, state_id, label, offset in self.saved_gotos:
			self.states[state_id].nextstate = (
				self.resolve_goto(line_number, label, offset))

	def parse(self, defstr):
		self.line_number = 1
		self.lines = defstr.split("\n")
		while self.more_lines():
			if (not self.parse_frame_def() and
			    not self.parse_loop() and
			    not self.parse_goto() and
			    not self.parse_stop()):
				self.exception("Parse error")
		if self.previous_state_id != -1:
			self.exception("sequence should end in stop, loop, "
			               "or goto")
		self.apply_gotos()

def parse(defstr):
	"""Parses a string in DECORATE-style States {} syntax.

	Returned is a tuple containing two values:
	 - A list of state_t instances corresponding to the states described in
	   the string. The references in 'nextstate' are indexed relative to
	   the list itself; these can be copied and remapped into another
	   states list using remap_states().
	 - A dictionary mapping from label names defined in the string to
	   indexes in the states list to the states they represent.
	"""
	p = _Parser()
	p.parse(defstr)
	return p.states, p.state_labels

def _generate_old_to_new(old, new, alloc_states):
	"""Generate old ID -> new ID mapping table.

	It's assumed that state 0 is always NULL.
	"""
	if len(old) - 1 > len(alloc_states):
		raise StateRemapException(
			"Can't remap %d states from old: only have %d free "
			"states to work with." % (
				len(old) - 1, len(alloc_states)))

	# Categorize states by whether they can have an action pointer:
	alloc_action = set()
	alloc_non_action = set()
	for state_id in alloc_states:
		if new[state_id].original().action is not None:
			alloc_action.add(state_id)
		else:
			alloc_non_action.add(state_id)

	# Build old->new map, allocating from alloc_action for states which
	# need an action, and from alloc_non_action for states which don't.
	old_to_new = [0] * len(old)
	for old_id in range(1, len(old)):
		if old[old_id].action is not None:
			if len(alloc_action) > 0:
				new_id = alloc_action.pop()
			else:
				# Won't work, unless BEX codeptrs are used:
				new_id = alloc_non_action.pop()
		else:
			if len(alloc_non_action) > 0:
				new_id = alloc_non_action.pop()
			else:
				# This is "wasteful" but there are no others:
				new_id = alloc_action.pop()
		old_to_new[old_id] = new_id
		alloc_states.remove(new_id)

	return old_to_new

def remap_states(old, new, alloc_states):
	"""Copy all states from old into new, remapping state IDs.

	alloc_states is a collection (list or set) of indexes into "new" which
	can be used to store the states copied from "old". Values are removed
	from this collection (via .pop()) that are consumed remapping states.

	The first state (old[0]) is not copied; it's assumed that state ID 0
	is a special value meaning NULL (S_NULL).
	"""
	old_to_new = _generate_old_to_new(old, new, alloc_states)

	# Copy over all states.
	for old_id in range(1, len(old)):
		new_id = old_to_new[old_id]
		new[new_id].copy_from(old[old_id])
		nextstate = new[new_id].nextstate
		# Update nextstate references:
		if nextstate != -1:
			new[new_id].nextstate = old_to_new[nextstate]

	return old_to_new

if __name__ == '__main__':
	states, labels = parse("""
	Spawn:
		TROO AB 10 A_Look
		Loop
	See:
		TROO AABBCCDD 3 A_Chase
		Loop
	Melee:
	Missile:
		TROO EF 8 A_FaceTarget
		TROO G 6 A_TroopAttack
		Goto See
	Pain:
		TROO H 2
		TROO H 2 A_Pain
		Goto See
	Death:
		TROO I 8
		TROO J 8 A_Scream
		TROO K 6
		TROO L 6 A_Fall
		TROO M -1
		Stop
	XDeath:
		TROO N 5
		TROO O 5 A_XScream
		TROO P 5
		TROO Q 5 A_Fall
		TROO RST 5
		TROO U -1
		Stop
	Raise:
		TROO MLKJI 8
		Goto See
	""")

	# Copy parsed states into table.
	import tables
	free_states = range(100, 200)
	old_to_new = remap_states(states, tables.states, free_states)
	labels = {name: old_to_new[i] for name, i in labels.items()}
	for label, start_id in labels.items():
		print "Label %r:" % label
		for state_id in tables.states.walk(start_id):
			print "\t%d: %s" % (state_id, tables.states[state_id])

