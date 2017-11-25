# pyNitel
python library to write Minitel servers/software

Inspired by Cristel and Dragster, my previous Minitel server software on Apple II and 68K Macintosh...

See:
- https://github.com/cquest/cristel
- https://github.com/cquest/dragster

*This code is extremely experimental !*

## Examples

### Annuaire

This example simulates the defunct "Annuaire Electronique", the videotex version of the phone directory.

*The goal*: use a Minitel to enter the name / location then query an existing phone directory on the web (118218.fr) and display the results on the Minitel as closest as possible to the original service back in the 80/90s.

*Status*:
- name/location input: not implemented yet
- query existing phone directory: implemented on 118218.fr and 118712.fr
- basic display: implemented
- display interaction (paging): not implemented

*To test*: `python3 example_annuaire.py "NAME" "LOCATION"`
