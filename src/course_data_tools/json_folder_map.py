from collections import OrderedDict
import hashlib
import json
import os

import structlog

logger = structlog.get_logger()


def json_folder_map(root, folder, name="index", dry_run=False):
    output = {
        "files": [],
        "type": "courses",
    }

    files = os.scandir(os.path.join(root, folder))
    for file in files:
        filename = file.name
        if filename.startswith("."):
            continue

        filepath = os.path.join(root, folder, filename)
        with open(filepath, "rb") as infile:
            basename, extension = os.path.splitext(filename)
            extension = extension[1:]  # splitext's extension includes the preceding dot

            info = {
                "path": f"terms/{filename}",
                "hash": hashlib.sha256(infile.read()).hexdigest(),
                "year": int(basename[0:4]),  # eg: 19943.json -> 1994
                "term": int(basename),  # eg: 19943.json -> 19943
                "type": extension,
            }

            output["files"].append(OrderedDict(sorted(info.items())))

    output["files"] = sorted(output["files"], key=lambda item: item["path"])
    output = OrderedDict(sorted(output.items()))

    logger.info("Hashed files")
    if dry_run:
        return

    index_path = os.path.join(root, f"{name}.json")
    with open(index_path, "w") as outfile:
        json.dump(output, outfile, indent="\t", ensure_ascii=False)
        outfile.write("\n")
        logger.info("Wrote %s", index_path)
