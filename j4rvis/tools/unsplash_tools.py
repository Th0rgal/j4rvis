import requests


def search_images_runner_builder(config):
    access_key = config["api"]["unsplash_access_key"]

    def search_images_runner(txt):
        query = "+".join(txt.split())  # Convert spaces in the query to '+'
        url = f"https://api.unsplash.com/search/photos?query={query}&client_id={access_key}"
        response = requests.get(url, timeout=10)
        data = response.json()
        results = data["results"]
        return str(
            [
                {
                    "description": x["description"]
                    if x["description"]
                    else x["alt_description"],
                    "full_image": x["urls"]["raw"],
                    "small_image": x["urls"]["small"],
                }
                for x in results
            ]
        )

    return search_images_runner
