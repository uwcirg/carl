"""Module to assist in paging through HAPI search bundles"""
from flask import current_app, has_app_context
import jmespath
import requests

from carl.config import FHIR_SERVER_URL
from carl.modules.resource import Resource


def next_page_link_from_bundle(bundle):
    next_page_link = jmespath.search("link[?relation=='next'].[url]", bundle)
    if not (next_page_link and len(next_page_link)):
        return

    # jmespath returns a list of matches, with the requested value at element zero
    return next_page_link[0][0]


def next_resource_bundle(resource_type, search_params=None):
    """Generate pages of search results, yielding bundles until exhausted

    :param resource_type: `Resource` object or string form of resource to look up, i.e. `Patient`
    :param search_params: optional search criteria to filter or order results
    :returns: bundle per page until exhausted
    """
    resource_string = (
        resource_type.RESOURCE_TYPE
        if isinstance(resource_type, Resource)
        else resource_type
    )
    url = f"{FHIR_SERVER_URL}{resource_string}"
    response = requests.get(url=url, params=search_params, timeout=30)
    if has_app_context():
        current_app.logger.debug(f"HAPI GET: {response.url}")
    response.raise_for_status()
    bundle = response.json()
    # yield first page
    yield bundle

    # continue yielding pages till exhausted
    while True:
        if "entry" not in bundle:
            return

        # get next page
        next_page_link = next_page_link_from_bundle(bundle)
        if not next_page_link:
            return

        response = requests.get(next_page_link, timeout=30)
        current_app.logger.debug(f"HAPI GET: {response.url}")
        response.raise_for_status()
        bundle = response.json()
        yield bundle
