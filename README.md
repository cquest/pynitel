# pyNitel
python library to write Minitel servers/software

Inspired by Cristel and Dragster, my previous Minitel server software on Apple II and 68K Macintosh...

See:
- https://github.com/cquest/cristel
- https://github.com/cquest/dragster

*This code is extremely experimental !*

## Examples

### Required hardware

Most Minitel have a serial port on a 5 pins DIN. This serial port is using TTL 5V levels.

Cheap USB / Serial TTL cables are available for a few dollars or euros, like https://www.kubii.fr/composants-raspberry-pi/1761-cable-usb-vers-ttl-4-pin-3272496006263.html

A 220K resistor is needed between the 5V and RX pin on the cable end (green and red wires), without it you can send data to the Minitel but cannot receive data.


### Annuaire

This example simulates the defunct "Annuaire Electronique", the videotex version of the phone directory.

**The goal**: use a Minitel to enter the name / location then query an existing phone directory on the web (118218.fr) and display the results on the Minitel as closest as possible to the original service back in the 80/90s.

**Status**:
- name/location input: implemented
- query existing phone directory: implemented on 118218.fr, 118712.fr ans 118000.fr
- basic display: implemented
- display interaction (paging): not implemented

**To test**: `python3 example_annuaire.py "NAME" "LOCATION"`
