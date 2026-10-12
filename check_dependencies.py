
import json
import urllib.request
import urllib.error
from datetime import datetime


def get_pypi_data(url):
    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "PyPI-Dependency-Checker/1.0"}
        )

        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        print(f"HTTP error for {url}: {error.code}")
        return None

    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        print(f"Request failed for {url}: {error}")
        return None


def main():
    filename = "requirements.txt"

    with open(filename, "r", encoding="utf-8") as file:
        lines = [
            line.strip()
            for line in file
            if line.strip() and not line.strip().startswith("#")
        ]

    checked = 0
    missing_packages = []
    missing_versions = []
    valid_releases = []

    for line in lines:
        if "==" not in line:
            print(f"Skipping unsupported requirement: {line}")
            continue

        name, version = line.split("==", 1)
        name = name.strip()
        version = version.strip()

        if not name or not version:
            print(f"Skipping invalid requirement: {line}")
            continue

        checked += 1

        package_url = f"https://pypi.org/pypi/{name}/json"
        package_data = get_pypi_data(package_url)

        if package_data is None:
            missing_packages.append(name)
            continue

        version_url = (
            f"https://pypi.org/pypi/{name}/{version}/json"
        )
        version_data = get_pypi_data(version_url)

        if version_data is None:
            missing_versions.append(f"{name}=={version}")
            continue

        urls = version_data.get("urls", [])
        if not urls:
            print(f"No release files found for {name}=={version}")
            continue

        upload_time = urls[0].get("upload_time")

        if not upload_time:
            print(f"No upload time found for {name}=={version}")
            continue

        try:
            year = datetime.fromisoformat(
                upload_time.replace("Z", "+00:00")
            ).year

            valid_releases.append((name, version, year))

        except ValueError:
            print(f"Invalid upload time for {name}=={version}")

    print("\n--- PyPI Dependency Check ---")
    print(f"Dependencies checked: {checked}")
    print(f"Packages not on PyPI: {missing_packages}")
    print(f"Versions not on PyPI: {missing_versions}")

    if valid_releases:
        oldest = min(valid_releases, key=lambda release: release[2])
        print(
            f"Oldest pinned release: "
            f"{oldest[0]}=={oldest[1]}({oldest[2]})"
        )
    else:
        print("Oldest pinned release: None")


if __name__ == "__main__":
    main()
