class CodeableConcept(object):
    """FHIR shim"""

    def __init__(self, coding=None):
        self.codes = []
        if coding:
            self.codes.append(coding)

    def __eq__(self, other):
        # Order doesn't matter
        return set(self.codes) == set(other.codes)

    def as_fhir(self):
        return {'coding': [c.as_fhir() for c in self.codes]}

    def value_param(self):
        """Akin to `search_url`, but to only return the value portion

        Codings are often nested attributes, use in a search filter as
        [parameter]=[system]|[code] - this method returns on the right
        side or `value` portion of that query string.

        See also https://www.hl7.org/fhir/search.html#token

        NB - it's only possible to search for a single coding within the
        codeable concept.  Therefore, an exception is raised if the
        instance doesn't contain exactly one coding.

        """
        if len(self.codes) != 1:
            raise ValueError(
                f"Require single coding to include {self} in search for value_param ")

        coding = self.codes[0]
        return f"{coding.system}|{coding.code}"

