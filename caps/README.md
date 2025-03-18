# Fox Capabilities
This module is the base application for capability permission system in Django. It is heavilly inspired
by [Capn'Proto documentation](https://capnproto.org) ([interesting paper](http://www.erights.org/elib/capability/ode/ode.pdf)).

Goal features:
- [ ] Local permission system: simplified permission system assuming database as a source of trust
- [ ] Rest API integration
- [ ] Class based views integration
- [ ] Test proofed

Other wanted features in different app
- [ ] Extensible Agent allowing to sign and verify
- [ ] External: through certificate chains of capabilities in references: signing and validating
- [ ] Authentication scheme that can be used in ActivityPub-like APIs.

## Architecture
This module declares differents models:
- `Agent`: represent someone or something that can act on objects;
- `Capability`: represent a single capability;
- `Object`: object that is accessed through capability (abstract class);
- `Reference`: reference to an object, generated per Object model class;

Object are always accessed through their reference, which specify the rights for an agent regarding the targetted object. Capabilities can be shared if specified by the reference's creator.

```python
from fox.caps.models import Object, Reference

class Publication(Object):
    title = fields.CharField(max_length=64)
    pub_date = fields.DateTime()

# true
isinstance(Publication.Reference, Reference)

obj = Publication.objects.ref(agent, ref_uuid)
```
