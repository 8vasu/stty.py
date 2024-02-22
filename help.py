#!/usr/bin/python3

import stty

if __name__ != "__main__":
    raise ImportError(f'Cannot import "{__name__}" as a module.')

control_character_value_help = f"""    POSSIBLE VALUES: a string or bytes object. If a string value is used, then it
                     must be a string of length 1, or a string of length 2 staring
                     with "^" (circumflex, caret) to represent a control character,
                     or the string "undef". Please check the manpage of stty(1) for
                     more details. If a value of type "bytes" is used, then it must
                     be of length 1.
"""

print("For details on the following attributes, "
      "check the manpage of stty(1) on your system.\n")

print("Stty attributes:\n")

for x, y in [("iflag", "input mode"),
             ("oflag", "output mode"),
             ("cflag", "control mode"),
             ("lflag", "local mode")]:
    print(f"  Boolean {y} attributes (possible values: True, False):")
    print(f"    {' '.join(sorted(stty.settings['boolean'][x]))}\n")

print("  Winsize attributes (possible values: any nonnegative integer):")
print(f"    {' '.join(sorted(stty.settings['winsize']))}\n")

print("  Non-canonical mode-related attributes (possible values: any nonnegative integer):")
print(f"    {' '.join(sorted(stty.settings['non_canonical']))}\n")

print("  CSIZE and *DLY attributes:")
heading1 = "ATTRIBUTE"
heading2 = "POSSIBLE VALUES"
csize_key = "csize"
csize_values = ", ".join(sorted([f'stty.{v}, "{v}"' for v in stty.settings["csize"]]))

padding = max(len(x) for x in stty.settings["delay_masks"])
padding = max(padding, len(csize_key), len(heading1))

# Print heading for the table.
print(f"    {heading1:^{padding}}  |  {heading2}")
# Print the CSIZE row.
print(f"    {csize_key:^{padding}}  |  {csize_values}")
# Print the *DLY rows.
for mask, maskvalset in stty.settings["delay_masks"].items():
    mask_values = ", ".join(sorted([f'stty.{v}, "{v}"' for v in maskvalset]))
    print(f"    {mask:^{padding}}  |  {mask_values}")

print("\n  Control character attributes:")
print(f"    ATTRIBUTES: {' '.join(sorted(stty.settings['control_character']))}")
print(control_character_value_help)

print("  Speed attributes:")
print(f"    ATTRIBUTES: {' '.join(sorted(stty.settings['speed']))}")
print(f"    POSSIBLE VALUES: {', '.join([str(n) for n in sorted(stty.settings['baud_rates'])])}")
