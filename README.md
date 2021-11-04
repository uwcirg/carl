# CARL

Named after Carl Linnaeus, considered by some as the "father of modern taxonimy", this project
embodies a ``condition classifier``; a logic engine capable of acting on trigger events, querying
an external FHIR store for state and generating conditions when appropriate, pushed back into
the same external FHIR store.

## Conditions

Start simple, in prototype style, with the intent to replace logic engine and related components
as the need arises.

### COPD & COPD Exacerbated

Determine if a Patient should receive a COPD Condition with the `cnics` namespace system
by looking for at least one `coding` from the following known COPD Condition codings:

- "system": "http://hl7.org/fhir/sid/icd-9-cm"
  - "code": "491"
  - "code": "491.0"
  - "code": "491.1"
  - "code": "491.2"
  - "code": "491.20"
  - "code": "491.21"
  - "code": "491.22"
  - "code": "491.8"
  - "code": "491.9"
  - "code": "492"
  - "code": "492.0"
  - "code": "492.8"
  - "code": "493.2"
  - "code": "493.20"
  - "code": "493.21"
  - "code": "493.22"
  - "code": "496"
- "system": "http://hl7.org/fhir/sid/icd-10-cm"
  - "code": "J41.0"
  - "code": "J41.1"
  - "code": "J41.8"
  - "code": "J42"
  - "code": "J43.0"
  - "code": "J43.1"
  - "code": "J43.2"
  - "code": "J43.8"
  - "code": "J43.9"
  - "code": "J44.0"
  - "code": "J44.1"
  - "code": "J44.9"
- "system": "http://snomed.info/sct"
  - "code": "404684003"
