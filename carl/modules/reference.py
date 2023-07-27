class Reference(object):
    """FHIR Referenced resource wrapper"""

    def __init__(self, ref):
        self.ref = ref

    def as_fhir(self):
        """returns FHIR representation of a referenced resource"""
        return {"reference": f"{self.ref.RESOURCE_TYPE}/{self.ref.id()}"}

    @classmethod
    def from_fhir(cls, data):
        """Deserialize from json (FHIR) data"""
        from carl.modules.patient import Patient
        ref_deets = data.get("reference", "/").split('/')
        if not ref_deets[0]:
            raise ValueError(f"can't deserialize reference: {data}")
        for cls in (Patient,):
            if cls.RESOURCE_TYPE == ref_deets[0]:
                ref = ref_deets[1]
                break
        if not ref:
            raise ValueError(f"don't know how to deserialize reference of type: {ref_deets[0]}")
        return cls(ref)

    def value_param(self):
        """As a search parameter, references are looked up by id alone"""
        return self.ref.id()
