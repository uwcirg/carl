# CARL
Named after Carl Linnaeus, considered by some as the "father of modern taxonimy", this project
embodies a `condition classifier`; a logic engine capable of acting on trigger events, querying
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

## How To Run
As a flask application, `carl` exposes HTTP routes as well as a number of command line
interface entry points.

These instructions assume a docker-compose deployment.  Simply eliminate the leading `dc exec`
portion of each command if deployed outside a docker container.

To view available HTTP routes:
```
sudo docker-compose exec carl flask routes
```

To view available CLI entry points:
```
sudo docker-compose exec carl flask --help
```

Especially useful for debugging or testing, obtain any single Patient `_id` from the configured
FHIR store, and process via:
```
curl -X PUT http://localhost:5000/classify/<Patient._id>/<site>
```

To process the entire set of Patient resources found in the configured FHIR store:
```
sudo docker-compose run carl flask classify
```

Complete example for site `uw`, captures both standard out and error to respective log files:
```
sudo docker-compose run carl flask classify uw > /var/log/cnics_to_fhir/carl.out 2> /var/log/cnics_to_fhir/carl.err
```

