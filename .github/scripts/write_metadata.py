import os
from github import Github, Auth
from parse_issue import parse_issue
from crosswalks import dict_to_metadata, dict_to_yaml
from copy_files import copy_files
from ruamel.yaml import YAML
import io
import json

# Environment variables
token = os.environ.get("GITHUB_TOKEN")
issue_number = int(os.environ.get("ISSUE_NUMBER"))
model_owner = os.environ.get("OWNER")
model_repo_name = os.environ.get("REPO")


# Get issue
auth = Auth.Token(token)
g = Github(auth=auth)
repo = g.get_repo("ModelAtlasofTheEarth/Model_Submission")
issue = repo.get_issue(number = issue_number)

# Get model repo
model_repo = g.get_repo(f"{model_owner}/{model_repo_name}")

# Parse issue
data, error_log = parse_issue(issue)

# Convert dictionary to metadata json
metadata = dict_to_metadata(data, flat_compact_crate=False)

#FOR TESTING - print out dictionary as a comment
issue.create_comment("# M@TE crate \n"+str(metadata))

# Move files to repo
model_repo.create_file("ro-crate-metadata.json","add ro-crate",metadata)
#we should do this this as part of the copy to website action
model_repo.create_file("website_material/ro-crate-metadata.json","add ro-crate",metadata)

#######
#Save the trail of metadata sources to .metadat_trail
issue_dict_str = json.dumps(data)
model_repo.create_file(".metadata_trail/issue_body.json","add issue_body", issue.body)
model_repo.create_file(".metadata_trail/issue_dict.json","add issue_dict", issue_dict_str)


#######
# Something like this for the web YAML
yaml = YAML(typ=['rt', 'string'])
yaml.preserve_quotes = True
#control the indentation...
yaml.indent(mapping=2, sequence=4, offset=2)
web_yaml_dict = dict_to_yaml(data)
# Use an in-memory text stream to hold the YAML content
stream = io.StringIO()
stream.write('---\n')
yaml.dump(web_yaml_dict, stream)
stream.write('---\n')
yaml_content_with_frontmatter = stream.getvalue()
commit_message = 'Add YAML file with front matter'
model_repo.create_file("website_material/index.md", commit_message, yaml_content_with_frontmatter)


# Copy web material to repo
copy_files(model_repo, "website_material/graphics/", data)



# Report creation of repository
issue.create_comment(f"Model repository created at https://github.com/{model_owner}/{model_repo_name}")
