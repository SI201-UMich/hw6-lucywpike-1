# SI 201 HW6 (APIs, JSON, and Caching)
# Your name: Lucy Pike
# Your student id: 03123721
# Your email: lucypike@umich.edu
# Who or what you worked with on this homework (including generative AI like ChatGPT):
# If you worked with generative AI also add a statement for how you used it.
# I used AI to help me understand the requirements for each of the functions to ensure each of the aspects were met effectively. 
# Did your use of GenAI on this assignment align with your goals and guidelines in your Gen AI contract? If not, why?
# Yes, my use of AI aligned with my GenAI contract because I used AI to help me understand the content and guide me when I was lost, which follows my contract. 

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
        with open(filename, "r", encoding="utf-8") as f:    # open the file for reading with utf-8 encoding 
            return json.load(f)                             # load the JSON data from the file and return it as a dictionary
    except:
        return {}                                           # if there is an error (file not found, invalid JSON), return an empty dictionary

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
    with open(filename, "w", encoding="utf-8") as f:        # open the file for writing with utf-8 encoding (will overwrite the file if it already exists)
        json.dump(dictionary, f)                            # convert the dictionary to JSON and write it to the file

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
    url = f"https://dogapi.dog/api/v2/breeds/{breed_id}"        # construct the URL for the API request using the given breed_id 
    try:
        response = requests.get(url)                            # send a GET request to the API and store the response
    except requests.RequestException:                           # if there is an error during the request, catch the exception and return None
        return None

    if response.status_code != 200:                             # if the response status code is not 200 (OK), return None
        return None

    try:
        parsed = response.json()                                # try to parse the response body as JSON and store it in the variable 'parsed'
    except ValueError:                                          # if there is an error during JSON parsing (invalid JSON), catch the exception and return None
        return None

    if parsed is None or parsed.get("data") is None:            # if the parsed JSON is None or does not contain a 'data' key, return None
        return None

    return (parsed, url)                                        # if everything is works, return a tuple containing the parsed JSON and the URL used for the request   

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
    cache = load_json(cache_file)                                   # load the existing cache from the given cache_file 
    if not isinstance(cache, dict):                                 # if the loaded cache is not a dictionary, treat it as an empty dictionary
        cache = {}                                             
    successful_adds = 0                                             # initialize a counter for successful additions to the cache and get the total number of breed_ids to process
    total = len(breed_ids)                                          # find the length of the breed_ids list and store it as total to calculate the percentage later

    for breed_id in breed_ids:                                      # loop through each breed_id in the breed_ids list
        url = f"https://dogapi.dog/api/v2/breeds/{breed_id}"        # construct the URL for the API request using the current breed_id
        if url in cache:                                            # if the URL is already a key in the cache, skip this breed_id and move to the next one
            continue

        result = search_breed(breed_id)                             # call the search_breed function with the current breed_id and store the result (which is either a tuple of parsed JSON and URL or None)
        if result is None:                                          # if the result is None (failed request or invalid response), skip this breed_id and move to the next one
            continue

        parsed_json, parsed_url = result                            # unpack the result tuple into parsed_json and parsed_url variables
        if parsed_json is None or parsed_json.get("data") is None:  # if the parsed JSON is None or does not contain a 'data' key, skip this breed_id and move to the next one
            continue

        cache[url] = parsed_json                                    # if the result is valid, add it to the cache with the URL as the key and the parsed JSON as the value
        successful_adds += 1                                        # increment the successful additions counter since it added a new entry to the cache

    create_cache(cache, cache_file)                                 # after processing all breed_ids, save the updated cache back to the cache_file using the create_cache function

    percent = 0.0                                                   # initialize the percentage variable to 0.0 to handle the case where total is 0 (avoids division by zero)
    if total > 0:                                                   # if total is greater than 0, calculate the percentage
        percent = (successful_adds / total) * 100                   # calculate the percentage of successful additions to the cache based on the total number of breed_ids processed and store it in the percent variable

    return f"Cached data for {percent}% of breeds"                  # return a formatted string indicating the percentage of breeds for which data was successfully cached

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
    cache = load_json(cache_file)                               # load the cache from the given cache_file using the load_json function
    if not isinstance(cache, dict) or not cache:                # if the loaded cache is not a dictionary or is empty, return "No breeds found" since there are no breeds to evaluate
        return "No breeds found"

    best_name = None                                            # initialize variables to keep track of the breed with the longest lifespan and its name
    best_life = None                                            # best_name will store the name of the breed with the longest lifespan and best_life will store the maximum lifespan value

    for item in cache.values():                                 # loop through each item in the cache (the values of the cache dictionary, which are the parsed JSON data for each breed)
        if not isinstance(item, dict):                          # if the current item is not a dictionary, skip it and move to the next one
            continue

        data = item.get("data")                                 # get the 'data' key from the current item and store it in the variable 'data'
        if not isinstance(data, dict):                          # if the 'data' value is not a dictionary, skip it and move to the next item in the cache
            continue

        attributes = data.get("attributes")                     # get the 'attributes' key from the 'data' dictionary and store it in the variable 'attributes'
        if not isinstance(attributes, dict):                    # if the 'attributes' value is not a dictionary, skip it and move to the next item in the cache
            continue

        name = attributes.get("name")                           # get the 'name' key from the 'attributes' dictionary and store it in the variable 'name'
        if not isinstance(name, str) or not name:               # if the 'name' value is not a string or is an empty string, skip it and move to the next item in the cache
            continue

        life = attributes.get("life")                           # get the 'life' key from the 'attributes' dictionary and store it in the variable 'life'
        if not isinstance(life, dict):                          # if the 'life' value is not a dictionary, skip it and move to the next item in the cache
            continue

        max_life = life.get("max")                              # get the 'max' key from the 'life' dictionary and store it in the variable 'max_life'
        if max_life is None:                                    # if the 'max' value is None (missing), skip it and move to the next item in the cache 
            continue
       
        try:
            numeric_max = int(max_life)                         # try to convert the 'max' value to an integer and store it in the variable 'numeric_max'
        except (ValueError, TypeError):                         # if there is an error during the conversion, catch the exception and skip this item by moving to the next one in the cache
            continue

        if (
            best_life is None                                   # if best_life is None (first valid breed found)
            or numeric_max > best_life                          # if the current breed's max lifespan is greater than the best_life found so far, update best_life and best_name to the current breed's values
            or (numeric_max == best_life and name < best_name)  # if there is a tie in max lifespan (numeric_max == best_life), compare the breed names alphabetically and update best_name to the current breed's name if it comes before the current best_name in alphabetical order
        ):
            best_life = numeric_max                             # update best_life to the current breed's max lifespan value since it's either the first valid breed found, has a longer lifespan than the current best, or is tied for longest but comes first alphabetically
            best_name = name                                    # update best_name to the current breed's name since it's either the first valid breed found, has a longer lifespan than the current best, or is tied for longest but comes first alphabetically

    if best_name is None:                                       # if after evaluating all breeds in the cache, best_name is still None (no valid breed with a max lifespan was found), return "No breeds found"
        return "No breeds found"

    return (best_name, best_life)                               # if a valid breed with a max lifespan was found, return a tuple containing the name of the breed with the longest lifespan and its maximum lifespan value (best_name, best_life)

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
    cache = load_json(cache_file)                                          # load the cache from the given cache_file using the load_json function
    if not isinstance(cache, dict):                                        # if the loaded cache is not a dictionary, return an empty dictionary 
        return {}

    group_counts = {}                                                      # initialize an empty dictionary to keep track of the count of breeds for each group; keys will be group UUIDs and the values will be the counts
    for entry in cache.values():                                           # loop through each entry in the cache (the values of the cache dictionary)
        if not isinstance(entry, dict):                                    # if the current entry is not a dictionary, skip it and move to the next one in the cache
            continue

        data = entry.get("data")                                           # get the 'data' key from the current entry and store it in the variable 'data'
        if not isinstance(data, dict):                                     # if the 'data' value is not a dictionary, skip it and move to the next entry in the cache
            continue

        relationships = data.get("relationships")                          # get the 'relationships' key from the 'data' dictionary and store it in the variable 'relationships'
        if not isinstance(relationships, dict):                            # if the 'relationships' value is not a dictionary, skip it and move to the next entry in the cache
            continue

        group = relationships.get("group")                                 # get the 'group' key from the 'relationships' dictionary and store it in the variable 'group'
        if not isinstance(group, dict):                                    # if the 'group' value is not a dictionary, skip it and move to the next entry in the cache
            continue

        group_data = group.get("data")                                     # get the 'data' key from the 'group' dictionary and store it in the variable 'group_data'
        if not isinstance(group_data, dict):                               # if the 'data' value in the 'group' dictionary is not a dictionary, skip it and move to the next entry in the cache
            continue

        group_id = group_data.get("id")                                    # get the 'id' key from the 'group_data' dictionary and store it in the variable 'group_id'
        if not isinstance(group_id, str) or not group_id:                  # if the 'id' value in the 'group_data' dictionary is not a string or is an empty string, skip it and move to the next entry in the cache
            continue

        group_counts[group_id] = group_counts.get(group_id, 0) + 1         # if the group_id is valid, update the count for that group_id in the group_counts dictionary by incrementing it by 1 (if the group_id is not already a key in the dictionary, get() will return 0, so it will start counting from 1)

    result = {}                                                            # initialize an empty dictionary to store the final result of groups that meet the cutoff criteria
    for gid, count in group_counts.items():                                # loop through each group_id and its corresponding count in the group_counts dictionary
        if count >= cutoff:                                                # if the count for the current group_id is greater than or equal to the cutoff value, add it to the result dictionary with the group_id as the key and the count as the value
            result[gid] = count
    return result                                                          # return the final result dictionary containing only the groups that have a count of breeds greater than or equal to the cutoff value   

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
    cache = load_json(cache_file)                                               # load the cache from the given cache_file using the load_json function
    if not isinstance(cache, dict) or not cache:                                # if the loaded cache is not a dictionary or is empty, return "No breed data found in cache."
        return "No breed data found in cache."

    target_breed = None                                                         # initialize a variable to keep track of the target breed entry in the cache that matches the given breed_name; start with None to indicate that it has not been found yet
    for entry in cache.values():                                                # loop through each entry in the cache (the values of the cache dictionary)
        if not isinstance(entry, dict):                                         # if the current entry is not a dictionary, skip it and move to the next one in the cache
            continue

        data = entry.get("data")                                                # get the 'data' key from the current entry and store it in the variable 'data'
        if not isinstance(data, dict):                                          # if the 'data' value is not a dictionary, skip it and move to the next entry in the cache
            continue

        attributes = data.get("attributes")                                     # get the 'attributes' key from the 'data' dictionary and store it in the variable 'attributes'
        if not isinstance(attributes, dict):                                    # if the 'attributes' value is not a dictionary, skip it and move to the next entry in the cache
            continue

        name = attributes.get("name")                                           # get the 'name' key from the 'attributes' dictionary and store it in the variable 'name'
        if not isinstance(name, str) or not name:                               # if the 'name' value is not a string or is an empty string, skip it and move to the next entry in the cache    
            continue

        if name.lower() == breed_name.lower():                                  # if the lowercase version of the current breed's name matches the lowercase version of the given breed_name, it's the target breed in the cache
            target_breed = entry                                                # set target_breed to the current entry in the cache that matches the breed_name
            break

    if target_breed is None:                                                    # if after evaluating all entries in the cache, target_breed is still None (no matching breed name was found), return "'{breed_name}' is not in the cache."
        return f"'{breed_name}' is not in the cache."

    relationships = target_breed.get("data", {}).get("relationships", {})       # get the 'relationships' key from the 'data' dictionary of the target_breed entry; if any of these keys are missing, use an empty dictionary as a default to avoid errors
    group_id = relationships.get("group", {}).get("data", {}).get("id")         # get the 'id' key from the 'data' dictionary of the 'group' relationship; if any of these keys are missing, use an empty dictionary as a default to avoid errors and store the group_id in the variable 'group_id'
    if not isinstance(group_id, str) or not group_id:                           # if the group_id is not a string or is an empty string, return "No group information available for '{breed_name}'."
        return f"No group information available for '{breed_name}'."            # if the target breed does not have valid group information, there's no recommendations based on group, so it returns the message

    recommendations = []                                                        # initialize an empty list to store the names of recommended breeds that are in the same group as the target breed
    for entry in cache.values():                                                # loop through each entry in the cache again to find other breeds that share the same group_id as the target breed
        if entry == target_breed:                                               # if the current entry is the same as the target_breed entry, skip it and move to the next one in the cache since it should exclude the target breed from the recommendations
            continue        

        data = entry.get("data", {})                                            # get the 'data' key from the current entry and store it in the variable 'data'; if 'data' is missing, use an empty dictionary as a default to avoid errors
        rels = data.get("relationships", {})                                    # get the 'relationships' key from the 'data' dictionary and store it in the variable 'rels'; if 'relationships' is missing, use an empty dictionary as a default to avoid errors
        gid = rels.get("group", {}).get("data", {}).get("id")                   # get the 'id' key from the 'data' dictionary of the 'group' relationship; if any of these keys are missing, use an empty dictionary as a default to avoid errors and store the group id in the variable 'gid'
        if gid == group_id:                                                     # if the group id of the current entry matches the group_id of the target breed, it means this breed is in the same group and should be recommended 
            name = data.get("attributes", {}).get("name")                       # get the 'name' key from the 'attributes' dictionary of the 'data' dictionary; if any of these keys are missing, use an empty dictionary as a default to avoid errors and store the name in the variable 'name'
            if isinstance(name, str) and name:                                  # if the name is a valid non-empty string, add it to the recommendations list
                recommendations.append(name)

    if not recommendations:                                                     # if after evaluating all entries in the cache, the recommendations list is still empty (no other breeds in the same group were found), return "No recommendations found based on '{breed_name}'."  
        return f"No recommendations found based on '{breed_name}'."      

    return sorted(recommendations)                                              # if there are valid recommendations, return the list of recommended breed names sorted alphabetically

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
        if os.path.exists(self.test_cache_file):
            os.remove(self.test_cache_file)

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

if __name__ == "__main__":
    unittest.main(verbosity=2)