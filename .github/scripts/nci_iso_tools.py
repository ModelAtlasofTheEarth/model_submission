class NestedDict(dict):
    def get_nested(self, keys):
        current = self
        for key in keys.split('.'):
            current = current.get(key, {})
        return current

def graph_to_nested_dict(graph):
    nested_dict = NestedDict()
    for item in graph:
        key = 'root' if item["@id"] == './' else item["@id"]
        nested_dict[key] = item
    return nested_dict

def list_to_string(value):
    if isinstance(value, list):
        return ', '.join(value)
    return value



def extract_creator_details(ro_crate_nested):
    creators = ro_crate_nested.get('root', {}).get('creator', [])
    creator_details = []
    for creator in creators:
        details = {
            "Last name": creator.get("familyName", "Unknown"),  # Default to "Unknown" if not provided
            "First name": creator.get("givenName", "Unknown"),  # Default to "Unknown" if not provided
            "Organization": creator.get("affiliation", {}).get("name", "Unknown") if "affiliation" in creator else "Unknown",
            "Email": creator.get("email", "Unknown"),  # Default to "Unknown" if not provided
            "ORCID ID": creator.get("@id", "Unknown")  # Default to "Unknown" if not provided
        }
        creator_details.append(details)
    return creator_details




def extract_funder_details(ro_crate_nested):
    funders = []

    # Extract 'funder' entries directly using NestedDict indexing
    root_funders = ro_crate_nested.get_nested('root.funder') or []
    for funder in root_funders:
        # Use the funder record directly if it doesn't have an '@id'
        if "@id" in funder:
            funder_details = ro_crate_nested.get(funder["@id"], {})
        else:
            funder_details = funder
        funders.append({
            "name": funder_details.get("name", "Unknown"),
            "grant_id": "No grant ID provided",  # Default text for missing grant IDs
            "email": "Email not provided"  # Default text assuming no email provided
        })

    # Extract 'funding' entries, which are typically grants
    root_fundings = ro_crate_nested.get_nested('root.funding') or []
    for funding in root_fundings:
        if "@id" in funding:
            funding_details = ro_crate_nested.get(funding["@id"], {})
            # Handle nested 'funder' information within 'funding'
            if "funder" in funding_details:
                if "@id" in funding_details["funder"]:
                    funder_info = ro_crate_nested.get(funding_details["funder"]["@id"], {})
                else:
                    funder_info = funding_details["funder"]
                funder_name = funder_info.get("name", "Unknown")
            else:
                funder_name = "Unknown"  # Default text if funder name is not available
            funders.append({
                "name": funder_name,
                "grant_id": funding_details.get("identifier", "No grant ID provided"),
                "email": "Email not provided"  # Default text assuming no email provided
            })

    # Deduplicate funders based on 'name'
    unique_funders = {funder['name']: funder for funder in funders if funder['name'] != "Unknown"}
    return list(unique_funders.values())
