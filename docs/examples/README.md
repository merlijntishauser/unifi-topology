# Example diagrams

Rendered from a real UniFi controller (10 devices, 40 clients, 50 nodes) and
then anonymized. Both files describe the same network, so they show what the
render options actually change on real data rather than on mock topologies.

| File | Options | Icon set |
| --- | --- | --- |
| `topology-tree-isopacks.svg` | defaults | `isometric` (isopacks) |
| `topology-compact-unifi.svg` | `iso_lighting=True, iso_compact_layout=True` | `unifi` |

The default layout puts this network on a single diagonal, because it maps
sibling order to one grid axis and tree depth to the other, and a home network
is shallow and wide. The compact layout packs each switch and its clients into
a district instead.

## Anonymization

The originals carried hardware MACs (33 distinct vendor OUIs), room names and
household members' first names. `generate_example.py` rebuilds the diagram with:

- every MAC replaced by a locally-administered `02:00:00:xx:xx:xx` address, which
  no vendor can be assigned and so identifies nothing
- every device name replaced by `<Type> <n>` (`Switch 1`, `Access Point 3`)
- edge labels reduced from `<device name>: Port 4` to `Port 4`

Node count, parent-child structure, port fan-out, VLANs, PoE and link speeds are
all preserved, so the layout and colouring are exactly what the real data
produces.

## Regenerating

Requires controller credentials in a `.env` (see the main README):

```bash
python docs/examples/generate_example.py docs/examples .env
```

Verify before committing --- the script is the only thing standing between the
controller and a public repository:

```bash
grep -oE '([0-9a-f]{2}:){5}[0-9a-f]{2}' docs/examples/*.svg | grep -v '02:00:00:'
```

That must print nothing.
