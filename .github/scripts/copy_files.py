import requests
from github.GithubException import UnknownObjectException
from pathlib import Path


def copy_files(repo,
               issue_dict,
               entry_list : list[str] = [],
               directory : str = '.website_material/',
               ):
    """
    Copies set GitHub Issue entries from the issue into the new repository.

    Iterates over a fixed set of entry keys. For each key present in issue_dict with a
    non-empty URL, the file is downloaded via HTTP and uploaded to the specified directory
    in the target repository. Files that already exist in the repository are silently
    skipped.

    Parameters:
        repo (github.Repository.Repository): A PyGithub Repository object representing the target GitHub repository. 
        directory (str): The directory path within the repository where files should be placed (e.g. '.website_material/').
        issue_dict (dict): A dictionary containing metadata about the model, including optional image/animation records with 'url' and 'filename' keys. 
        entry_list (list): List of entry name from the issue to copy to the new repository at location 'directory'. (e.g. '["landing_image", "animation", "graphic_abstract", "model_setup_figure"]').

    Returns:
        None
    """

    for entry in entry_list:
        if entry in issue_dict:
            # assume issue entry has url and filename
            url = issue_dict[entry].get("url")
            fname = issue_dict[entry].get("filename")

            # Skip if the URL is an empty string
            if url:
                suffix = Path(fname).suffix
                save_path = directory + entry

                # Skip if file already exists in repo's save_path
                file_exists = False
                try:
                    _ = repo.get_contents(save_path)
                    file_exists = True
                except UnknownObjectException:
                    file_exists = False

                if file_exists:
                    print(f"Skipping {entry} as the file already exists")
                else:
                    response = requests.get(url)
                    new_path = save_path + suffix
                    repo.create_file(
                        new_path,
                        f"add {fname} to {new_path}",
                        response.content,
                    )
            else:
                print(f"Skipping {entry} as the URL is empty")
