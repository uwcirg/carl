class Reference(object):
    """FHIR Referenced resource wrapper"""
    def __init__(self, ref):
        self.ref = ref

    def as_fhir(self):
        """returns FHIR representation of a referenced resource"""
        return {"reference": f"{self.ref.RESOURCE_TYPE}/{self.ref.id()}"}

    def value_param(self):
        """As a search parameter, references are looked up by id alone"""
        return self.ref.id()
