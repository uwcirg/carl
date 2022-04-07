# CARL
Named after Carl Linnaeus, considered by some as the "father of modern taxonimy", this project
embodies a `condition classifier`; a logic engine capable of acting on trigger events, querying
an external FHIR store for state and generating conditions when appropriate, pushed back into
the same external FHIR store.

## Marker Conditions
### "COPD" & "COPD, exacerbation" Condition

Patients found to have at least one condition from the CNICS COPD Value Set,
are marked with a [Condition](https://www.hl7.org/fhir/condition.html) with `code`:

```
{
    system="https://cpro.cirg.washington.edu/groups",
    code="CNICS.COPD2021.11.001",
    display="COPD PRO group member",
}
```

Example FHIR Query to obtain [FHIR Patients](https://www.hl7.org/fhir/patient.html) having said condition:
```
https://SERVER/fhir/Patient?_has:Condition:patient:code=CNICS.COPD2021.11.001
```
### COPD MedicationRequest

Patients found to have at least one [MedicationRequest](https://www.hl7.org/fhir/medicationrequest.html)
from the CNICS COPD Medication Value Set, are marked with a
[Condition](https://www.hl7.org/fhir/condition.html) with `code`:

```
{
    system="https://cpro.cirg.washington.edu/groups",
    code="CNICS.COPDMED2022.03.001",
    display="COPD Medication group member",
}
```

## ValueSets
### CNICS COPD Value Set
List of qualifying COPD and COPD exacerbation condition codings.
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

### CNICS COPD Medication Value Set
List of qualifying COPD MedicationRequest codings.
- "system": "https://cnics.cirg.washington.edu/medication-name"
  - "code": "IPRATROPIUM-INHALED"
  - "code": "ARFORMOTEROL"
  - "code": "FORMOTEROL"
  - "code": "OLODATEROL"
  - "code": "SALMETEROL"
  - "code": "ACLIDINIUM"
  - "code": "TIOTROPIUM"
  - "code": "UMECLIDINIUM"
  - "code": "FLUTICASONE FUROATE + UMECLIDINIUM + VILANTEROL"
  - "code": "ALBUTEROL + IPRATROPIUM"
  - "code": "IPRATROPIUM +  FENOTEROL"
  - "code": "ACLIDINIUM + FORMOTEROL"
  - "code": "BUDESONIDE + FORMOTEROL"
  - "code": "FLUTICASONE + SALMETEROL"
  - "code": "FLUTICASONE + VILANTEROL"
  - "code": "MOMETASONE + FORMOTEROL"
  - "code": "OLODATEROL + TIOTROPIUM"
  - "code": "UMECLIDINIUM +  VILANTEROL"
  - "code": "GLYCOPYRROLATE + FORMOTEROL FUMARATE"


## How To Run
As a flask application, `carl` exposes HTTP routes as well as a number of command line
interface entry points.

These instructions assume a docker-compose deployment.  Simply eliminate the leading `dc exec`
portion of each command if deployed outside a docker container.

To view available HTTP routes:
```
docker-compose exec carl flask routes
```

To view available CLI entry points:
```
docker-compose exec carl flask --help
```

Especially useful for debugging or testing, obtain any single Patient `_id` from the configured
FHIR store, and process via:
```
curl -X PUT http://localhost:5000/classify/<Patient._id>/<site>
```

To process the entire set of Patient resources found in the configured FHIR store:
```
docker-compose run carl flask classify
```

To reset, that is remove conditions added from previous runs:
```
docker-compose run carl flask declassify
```

Complete example for site `uw`, captures both standard out and error to respective log files:
```
docker-compose run carl flask classify uw > /var/log/cnics_to_fhir/carl.out 2> /var/log/cnics_to_fhir/carl.err
```
