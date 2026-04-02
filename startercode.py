# SI 201 HW6 (APIs, JSON, and Caching)
# Your name: Lucy Pike
# Your student id: 03123721
# Your email: lucypike@umich.edu
# Who or what you worked with on this homework (including generative AI like ChatGPT):
# If you worked with generative AI also add a statement for how you used it.
# 
# Did your use of GenAI on this assignment align with your goals and guidelines in your Gen AI contract? If not, why?
#
# --- ARGUMENTS & EXPECTED RETURN VALUES PROVIDED --- #
# --- SEE INSTRUCTIONS FOR FULL DETAILS ON METHOD IMPLEMENTATION --- #

import requests
import json
import unittest
import os

from dogapi_sample_cache import (
    SAMPLE_CACHE,
    GROUP_ID_HOUND,
    GROUP_ID_TOY,
    GROUP_ID_HERDING,
)


def load_json(filename):
    """
    Opens the given file and loads its contents as a Python dictionary using json.load.

    ARGUMENTS:
        filename: path/name of the JSON file to read (use utf-8 encoding)

    RETURNS:
        A dictionary with the JSON data, OR an empty dictionary {} if the file
        cannot be opened or is not valid JSON.
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def create_cache(dictionary, filename):
    """
    Converts a Python dictionary into JSON and writes it to filename (overwrites the
    file if it already exists). Used to save the breed cache to disk.

    ARGUMENTS:
        dictionary: the cache dictionary (keys are often request URLs, values are API JSON)
        filename: the file to write to

    RETURNS:
        None
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(dictionary, f)

def search_breed(breed_id):
    """
    Sends a GET request to the Dog API v2 for a single breed:
        https://dogapi.dog/api/v2/breeds/{breed_id}
    Breed ids are UUID strings in the live API.

    ARGUMENTS:
        breed_id: the breed id to request (string UUID from the API or your id list file)

    RETURNS:
        A tuple (parsed_json_dict, response_url) where the first element is the full
        JSON body as a dict (with a top-level 'data' key on success), OR None if the
        request failed or the response does not represent a successful breed lookup.
    """
    url = f"https://dogapi.dog/api/v2/breeds/{breed_id}"
    try:
        response = requests.get(url)
    except requests.RequestException:
        return None

    if response.status_code != 200:
        return None

    try:
        parsed = response.json()
    except ValueError:
        return None

    if parsed is None or parsed.get("data") is None:
        return None

    return (parsed, url)

def update_cache(breed_ids, cache_file):
    """
    For each breed_id, fetch data from the API and add it to the cache if not already present.
    Skip requests for breeds whose URL is already in the cache. Only count newly added,
    successful results. After processing all IDs, save the updated cache.

    ARGUMENTS:
        breed_ids: list of breed id strings to fetch
        cache_file: path to the JSON cache file (may not exist yet; treat missing as {})

    RETURNS:
        A string: "Cached data for {percentage}% of breeds",
        where percentage = (successful_new_adds / len(breed_ids)) * 100.
    """
    cache = load_json(cache_file)
    if not isinstance(cache, dict):
        cache = {}

    successful_adds = 0
    total = len(breed_ids)

    for breed_id in breed_ids:
        url = f"https://dogapi.dog/api/v2/breeds/{breed_id}"
        if url in cache:
            continue

        result = search_breed(breed_id)
        if result is None:
            continue

        parsed_json, parsed_url = result
        if parsed_json is None or parsed_json.get("data") is None:
            continue

        cache[url] = parsed_json
        successful_adds += 1

    create_cache(cache, cache_file)

    percent = 0.0
    if total > 0:
        percent = (successful_adds / total) * 100

    return f"Cached data for {percent}% of breeds"

def get_longest_lifespan_breed(cache_file):
    """
    For the breeds currently stored in the cache, this function finds the breed with the highest maximum lifespan.
    If there is a tie, it returns the breed that comes first in alphabetical order.

    ARGUMENTS:
        cache_file: path to the JSON cache file

    RETURNS:
        A tuple (breed_name, max_lifespan_integer) for the winning breed, OR the
        string "No breeds found" if no breed in the cache has a life.max value.
    """
    cache = load_json(cache_file)
    if not isinstance(cache, dict) or not cache:
        return "No breeds found"

    best_name = None
    best_life = None

    for item in cache.values():
        if not isinstance(item, dict):
            continue

        data = item.get("data")
        if not isinstance(data, dict):
            continue

        attributes = data.get("attributes")
        if not isinstance(attributes, dict):
            continue

        name = attributes.get("name")
        if not isinstance(name, str) or not name:
            continue

        life = attributes.get("life")
        if not isinstance(life, dict):
            continue

        max_life = life.get("max")
        if max_life is None:
            continue

        try:
            numeric_max = int(max_life)
        except (ValueError, TypeError):
            continue

        if best_life is None or numeric_max > best_life or (
            numeric_max == best_life and name < best_name
        ):
            best_life = numeric_max
            best_name = name

    if best_name is None:
        return "No breeds found"

    return (best_name, best_life)

def get_groups_above_cutoff(cutoff, cache_file):
    """
    Counts how many cached breeds belong to each Dog API group, then keeps only
    groups whose count is greater than or equal to cutoff.

    In Dog API v2, a breed's group is not a string in attributes; it is linked via:
        data.relationships.group.data.id   (a group UUID string)
    Skip any cache entry that has no group relationship or no id there.

    ARGUMENTS:
        cutoff: minimum number of breeds a group must have to appear in the result
        cache_file: path to the JSON cache file

    RETURNS:
        A dictionary {group_uuid: count} for groups with count >= cutoff only.
    """
    cache = load_json(cache_file)
    if not isinstance(cache, dict):
        return {}

    group_counts = {}
    for entry in cache.values():
        if not isinstance(entry, dict):
            continue

        data = entry.get("data")
        if not isinstance(data, dict):
            continue

        relationships = data.get("relationships")
        if not isinstance(relationships, dict):
            continue

        group = relationships.get("group")
        if not isinstance(group, dict):
            continue

        group_data = group.get("data")
        if not isinstance(group_data, dict):
            continue

        group_id = group_data.get("id")
        if not isinstance(group_id, str) or not group_id:
            continue

        group_counts[group_id] = group_counts.get(group_id, 0) + 1

    result = {}
    for gid, count in group_counts.items():
        if count >= cutoff:
            result[gid] = count
    return result

# Extra Credit
def recommend_breeds_in_same_group(breed_name, cache_file):
    """
    Recommends other breeds in the cache that share the same Dog API group id as
    the given breed. Match the target breed by data["attributes"]["name"] (case-insensitive).
    Compare groups using data["relationships"]["group"]["data"]["id"] (UUID).
    Exclude the target breed in the result list.
    Return breed names sorted alphabetically.

    ARGUMENTS:
        breed_name: the breed name to look up in the cache
        cache_file: path to the JSON cache file

    RETURNS:
        EITHER a sorted list of other breed names in the same group
        OR one of these strings:
            "No breed data found in cache."  (empty cache)
            "'{breed_name}' is not in the cache."  (name not found)
            "No group information available for '{breed_name}'."  (no group id)
            "No recommendations found based on '{breed_name}'."  (no other breeds in that group)
    """


class TestHomeworkDogAPI(unittest.TestCase):
    def setUp(self):
        self.test_cache_file = "test_cache_dogs.json"

        # Real Dog API v2 breed IDs (UUID format)
        self.valid_breed_id_1 = "036feed0-da8a-42c9-ab9a-57449b530b13"  # Affenpinscher
        self.valid_breed_id_2 = "dd9362cc-52e0-462d-b856-fccdcf24b140"  # Afghan Hound

        # Real Dog API v2 group ids (shape matches relationships.group.data.id)
        self.group_id_hound = GROUP_ID_HOUND
        self.group_id_toy = GROUP_ID_TOY
        self.group_id_herding = GROUP_ID_HERDING

        # Shared fake cache for unit tests
        self.sample_cache = SAMPLE_CACHE

    def tearDown(self):
        # NOTE: By default we leave test files on disk so you can inspect the cache.
        # If you want the tests to clean up after themselves, UNCOMMENT the lines below.
        #
        # if os.path.exists(self.test_cache_file):
        #     os.remove(self.test_cache_file)
        pass

    # -------------------------
    # load_json / create_cache
    # -------------------------

    def test_load_and_create_cache(self):
        test_dict = {"test": [1, 2, 3]}
        create_cache(test_dict, self.test_cache_file)
        self.assertTrue(os.path.exists(self.test_cache_file))
        loaded = load_json(self.test_cache_file)
        self.assertEqual(loaded, test_dict)

    def test_load_json_returns_empty_dict_for_missing_or_invalid(self):
        # Missing file -> {}
        missing_file = "this_file_should_not_exist_123456.json"
        if os.path.exists(missing_file):
            os.remove(missing_file)
        self.assertEqual(load_json(missing_file), {})

        # Invalid JSON file -> {}
        invalid_file = "this_file_should_not_parse_123456.json"
        with open(invalid_file, "w", encoding="utf-8") as f:
            f.write("{ not valid json ")
        self.assertEqual(load_json(invalid_file), {})
        if os.path.exists(invalid_file):
            os.remove(invalid_file)

    # -------------------------
    # search_breed
    # -------------------------
    def test_search_breed(self):
        breed_data = search_breed(self.valid_breed_id_1)
        self.assertIsNotNone(breed_data)
        self.assertIsInstance(breed_data, tuple)
        self.assertEqual(len(breed_data), 2)

        parsed_json, url = breed_data

        self.assertIsInstance(parsed_json, dict)
        self.assertEqual(
            url, f"https://dogapi.dog/api/v2/breeds/{self.valid_breed_id_1}"
        )

        self.assertIn("data", parsed_json)
        self.assertIsNotNone(parsed_json["data"])
        self.assertEqual(parsed_json["data"]["id"], self.valid_breed_id_1)
        self.assertIn("attributes", parsed_json["data"])
        self.assertIn("name", parsed_json["data"]["attributes"])

    def test_search_breed_failure_returns_none(self):
        # Use an id that should not exist in the live API.
        out = search_breed("00000000-0000-0000-0000-000000000000")
        self.assertIsNone(out)

    # -------------------------
    # update_cache
    # -------------------------
    def test_update_cache(self):
        breed_ids = ["1", "2"]
        response = update_cache(breed_ids, self.test_cache_file)
        self.assertTrue("Cached data for" in response)

        cache = load_json(self.test_cache_file)
        self.assertIsInstance(cache, dict)

    def test_update_cache_updates_cache_file_and_percentage(self):
        # Start from an empty cache file.
        # Use real breed ids so this test doesn't need mocking.
        create_cache({}, self.test_cache_file)

        breed_ids = [self.valid_breed_id_1, self.valid_breed_id_2]
        resp = update_cache(breed_ids, self.test_cache_file)

        cache = load_json(self.test_cache_file)
        self.assertTrue(isinstance(cache, dict))
        self.assertEqual(len(cache), 2)

        expected_urls = [
            f"https://dogapi.dog/api/v2/breeds/{self.valid_breed_id_1}",
            f"https://dogapi.dog/api/v2/breeds/{self.valid_breed_id_2}",
        ]
        self.assertEqual(set(cache.keys()), set(expected_urls))
        self.assertEqual(resp, "Cached data for 100.0% of breeds")

    def test_update_cache_partial_success_percentage(self):
        create_cache({}, self.test_cache_file)

        breed_ids = [self.valid_breed_id_1, "00000000-0000-0000-0000-000000000000"]
        resp = update_cache(breed_ids, self.test_cache_file)

        cache = load_json(self.test_cache_file)
        self.assertEqual(len(cache), 1)
        self.assertEqual(resp, "Cached data for 50.0% of breeds")

    def test_update_cache_all_invalid_ids(self):
        create_cache({}, self.test_cache_file)

        breed_ids = [
            "00000000-0000-0000-0000-000000000000",
            "ffffffff-ffff-ffff-ffff-ffffffffffff",
        ]
        resp = update_cache(breed_ids, self.test_cache_file)

        cache = load_json(self.test_cache_file)
        self.assertEqual(cache, {})
        self.assertEqual(resp, "Cached data for 0.0% of breeds")

    def test_update_cache_no_duplicate_add(self):
        pre_url = f"https://dogapi.dog/api/v2/breeds/{self.valid_breed_id_1}"
        create_cache(
            {pre_url: {"data": {"id": self.valid_breed_id_1}}}, self.test_cache_file
        )

        breed_ids = [self.valid_breed_id_1, self.valid_breed_id_2]
        resp = update_cache(breed_ids, self.test_cache_file)

        cache = load_json(self.test_cache_file)
        self.assertEqual(len(cache), 2)  # only one new entry should be added
        self.assertEqual(resp, "Cached data for 50.0% of breeds")

    # -------------------------
    # get_longest_lifespan_breed
    # -------------------------

    def test_get_longest_lifespan_breed(self):
        create_cache(self.sample_cache, self.test_cache_file)
        result = get_longest_lifespan_breed(self.test_cache_file)
        self.assertEqual(result, ("Breed C", 16))

    def test_get_longest_lifespan_breed_no_breeds(self):
        create_cache({}, self.test_cache_file)
        self.assertEqual(
            get_longest_lifespan_breed(self.test_cache_file), "No breeds found"
        )

    def test_get_longest_lifespan_breed_tie_breaks_alphabetically(self):
        cache = {
            "url1": {"data": {"attributes": {"name": "Zulu", "life": {"max": 16}}}},
            "url2": {
                "data": {"attributes": {"name": "Affenpinscher", "life": {"max": 16}}}
            },
            "url3": {"data": {"attributes": {"name": "Beagle", "life": {"max": 12}}}},
        }
        create_cache(cache, self.test_cache_file)
        self.assertEqual(
            get_longest_lifespan_breed(self.test_cache_file), ("Affenpinscher", 16)
        )

    def test_get_longest_lifespan_breed_no_valid_lifespan_data(self):
        cache = {
            "url1": {"data": {"attributes": {"name": "Breed A"}}},
            "url2": {"data": {"attributes": {"name": "Breed B", "life": {}}}},
            "url3": {
                "data": {"attributes": {"name": "Breed C", "life": {"max": "long"}}}
            },
            "url4": {"data": {"attributes": {"name": "Breed D", "life": {"min": 10}}}},
        }

        create_cache(cache, self.test_cache_file)
        self.assertEqual(
            get_longest_lifespan_breed(self.test_cache_file), "No breeds found"
        )

    # -------------------------
    # get_groups_above_cutoff
    # -------------------------
    def test_get_groups_above_cutoff(self):
        create_cache(self.sample_cache, self.test_cache_file)

        test_1 = get_groups_above_cutoff(2, self.test_cache_file)
        self.assertEqual(test_1, {self.group_id_hound: 2})

        test_2 = get_groups_above_cutoff(1, self.test_cache_file)
        self.assertEqual(test_2[self.group_id_hound], 2)
        self.assertEqual(test_2[self.group_id_toy], 1)
        self.assertEqual(test_2[self.group_id_herding], 1)

        test_3 = get_groups_above_cutoff(3, self.test_cache_file)
        self.assertEqual(test_3, {})

    def test_get_groups_above_cutoff_ignores_invalid_group_entries(self):
        cache = {
            "url1": {"data": {"relationships": {"group": {"data": {"id": "g1"}}}}},
            "url2": {"data": {"relationships": {"group": {"data": {"id": "g1"}}}}},
            "url3": {"data": {"relationships": {"group": {"data": {}}}}},
            "url4": {"data": {"relationships": {"group": {}}}},
            "url5": {"data": {"relationships": {}}},
            "url6": {"data": {}},
            "url7": {},
        }
        create_cache(cache, self.test_cache_file)

        self.assertEqual(get_groups_above_cutoff(1, self.test_cache_file), {"g1": 2})
        self.assertEqual(get_groups_above_cutoff(2, self.test_cache_file), {"g1": 2})
        self.assertEqual(get_groups_above_cutoff(3, self.test_cache_file), {})

    # -------------------------
    # extra credit - uncomment tests below to evaluate extra credit function
    # -------------------------
    """
    def test_recommend_breeds_in_same_group_empty_cache(self):
        create_cache({}, self.test_cache_file)
        self.assertEqual(
            recommend_breeds_in_same_group("Breed A", self.test_cache_file),
            "No breed data found in cache.",
        )

    def test_recommend_breeds_in_same_group_name_not_found(self):
        cache = {
            "url1": {
                "data": {
                    "attributes": {"name": "Breed A"},
                    "relationships": {"group": {"data": {"id": "g1"}}},
                }
            }
        }
        create_cache(cache, self.test_cache_file)
        self.assertEqual(
            recommend_breeds_in_same_group("Breed X", self.test_cache_file),
            "'Breed X' is not in the cache.",
        )

    def test_recommend_breeds_in_same_group_no_group(self):
        cache = {"url1": {"data": {"attributes": {"name": "Breed A"}}}}
        create_cache(cache, self.test_cache_file)
        self.assertEqual(
            recommend_breeds_in_same_group("Breed A", self.test_cache_file),
            "No group information available for 'Breed A'.",
        )

    def test_recommend_breeds_in_same_group_no_matches(self):
        cache = {
            "url1": {
                "data": {
                    "attributes": {"name": "Breed A"},
                    "relationships": {"group": {"data": {"id": "g1"}}},
                }
            },
            "url2": {
                "data": {
                    "attributes": {"name": "Breed B"},
                    "relationships": {"group": {"data": {"id": "g2"}}},
                }
            },
        }
        create_cache(cache, self.test_cache_file)
        self.assertEqual(
            recommend_breeds_in_same_group("Breed A", self.test_cache_file),
            "No recommendations found based on 'Breed A'.",
        )

    def test_recommend_breeds_in_same_group_sorted(self):
        cache = {
            "url1": {
                "data": {
                    "attributes": {"name": "Breed A"},
                    "relationships": {"group": {"data": {"id": "g1"}}},
                }
            },
            "url2": {
                "data": {
                    "attributes": {"name": "Breed Z"},
                    "relationships": {"group": {"data": {"id": "g1"}}},
                }
            },
            "url3": {
                "data": {
                    "attributes": {"name": "Breed B"},
                    "relationships": {"group": {"data": {"id": "g1"}}},
                }
            },
        }
        create_cache(cache, self.test_cache_file)
        self.assertEqual(
            recommend_breeds_in_same_group("Breed A", self.test_cache_file),
            ["Breed B", "Breed Z"],
        )

    def test_recommend_breeds_in_same_group_case_insensitive_name_match(self):
        cache = {
            "url1": {
                "data": {
                    "attributes": {"name": "Breed A"},
                    "relationships": {"group": {"data": {"id": "g1"}}},
                }
            },
            "url2": {
                "data": {
                    "attributes": {"name": "Breed B"},
                    "relationships": {"group": {"data": {"id": "g1"}}},
                }
            },
            "url3": {
                "data": {
                    "attributes": {"name": "Breed Z"},
                    "relationships": {"group": {"data": {"id": "g1"}}},
                }
            },
        }
        create_cache(cache, self.test_cache_file)
        self.assertEqual(
            recommend_breeds_in_same_group("breed a", self.test_cache_file),
            ["Breed B", "Breed Z"],
        )
    """


if __name__ == "__main__":
    unittest.main(verbosity=2)
