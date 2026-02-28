# LitePolis Router Template

This repository serves as a template for creating router modules for LitePolis using `pyproject.toml` for packaging. It provides a basic structure and example code to guide you through the process of building your own API endpoints.

> :warning: Keep the prefix "litepolis-router-" and "litepolis_router_" in the name of package and directories to ensure the LitePolis package manager will be able to recognize it during deployment.

## Getting Started

1.  **Clone the Repository:** Start by cloning this repository to your local machine. (assuming you have installed `litepolis` from PyPI)
```bash
litepolis-cli create router LitePolis-router-dashboard
```

2.  **Rename the Package:** Update the package name and details in the following files:
    * **`pyproject.toml`**: Update the `version`, `description`, and `authors` fields within the same `[project]` table. Update the `Homepage` URL under `[project.urls]` if necessary.
    * **`tests/test_core.py`**: Update the import statement to reflect your new package name. For example, change `from litepolis_router_template import router, prefix` to `from litepolis_router_dashboard import router, prefix`.

3.  **Implement API Logic:** Modify the `litepolis_router_dashboard/core.py` file to implement your API routes and logic. Use the provided FastAPI `router` instance to define your endpoints (`@router.get`, `@router.post`, etc.) and necessary business logic. The `DEFAULT_CONFIG` dictionary in `core.py` allows for default configuration settings. Ensure you update the docstrings for your endpoints to accurately reflect their functionality, as these will be used to generate API documentation.

4.  **Testing:** The `tests/test_core.py` file contains example tests using Pytest and FastAPI's `TestClient`. Update these tests to cover your module's functionality. Ensure your tests correctly use `DEFAULT_CONFIG` where necessary and properly set up the FastAPI test application instance by including your `router` for testing. Ensure the tests run successfully after making changes.

## Important Considerations

* **API Documentation:** Well-documented code is crucial. Ensure your endpoints in `core.py` have clear and comprehensive docstrings (following FastAPI/Pydantic conventions). These docstrings will be used by LitePolis to generate interactive API documentation (like Swagger UI/ReDoc). For best practices and detailed examples, refer to this helpful resource: [How to Document an API for Python FastAPI](https://medium.com/codex/how-to-document-an-api-for-python-fastapi-best-practices-for-maintainable-and-readable-code-a183a3f7f036)

* **Testing:** Write comprehensive tests to cover all aspects of your router module, including different HTTP methods, request payloads, path parameters, query parameters, and expected responses (success and error cases).

* **Dependencies:** If your module requires external Python libraries (like database drivers, utility libraries, etc.), add them to the `dependencies` list under the `[project]` table in `pyproject.toml`. FastAPI-specific dependencies (using `Depends`) should still be defined in the `litepolis_router_template/dependencies.py` file (or your renamed version) as described below.

* **`DEFAULT_CONFIG` and Router:** The `DEFAULT_CONFIG` dictionary defined in `core.py` is crucial. Its contents will be registered with the LitePolis configuration system upon deployment. Ensure it contains appropriate default values for your service. The FastAPI `router` object defined in `core.py` is also essential, as LitePolis will discover it and include its routes in the main application, typically prefixed automatically based on your package name.

## About `dependencies`

This list `dependencies` is where you should list FastAPI dependencies needed by your API endpoints (e.g., getting the current user, establishing a database session). Listing them here helps LitePolis manage and inject dependencies during deployment.

## About `DEFAULT_CONFIG`

This dictionary, defined in `core.py`, holds default configuration values for your router module. These values will be registered with the LitePolis configuration system when the module is deployed. If modified configurations are provided during deployment, they will override these defaults. Settings can be fetched within your API endpoint functions (or dependency functions) using the `get_config(<package-name>, <configuration-key>)` function provided by LitePolis infrastructure, which will return the currently active value (live or default).

## Recommended Pattern for Accessing Configuration

To ensure automated tests (Pytest) do not rely on live configuration sources and use predictable values, employ the following pattern within your API logic or dependency functions when you need to fetch configuration values:

```python
import os
# Assuming get_config is available for fetching live config in a LitePolis env
# from litepolis import get_config

# Default config defined in your core.py
# from .core import DEFAULT_CONFIG

# Example Configuration Keys (should match keys in DEFAULT_CONFIG)
DB_URL_KEY = "database_url"
API_KEY_KEY = "some_api_key"

# --- Configuration Fetching Logic ---
db_url = None
some_key = None

# Check if running under Pytest
if ("PYTEST_CURRENT_TEST" not in os.environ and
    "PYTEST_VERSION" not in os.environ):
    # NOT running under Pytest: Fetch from live source
    print("Fetching configuration from live source...") # Optional debug msg
    # Replace 'litepolis-router-dashboard' with YOUR actual package name from pyproject.toml
    # db_url = get_config("litepolis-router-dashboard", DB_URL_KEY)
    # some_key = get_config("litepolis-router-dashboard", API_KEY_KEY)
    # Example placeholder if get_config isn't immediately available:
    db_url = "live_db_url_placeholder"
    some_key = "live_api_key_placeholder"
else:
    # Running under Pytest: Use default values from DEFAULT_CONFIG
    print("Running under Pytest. Using default configuration.") # Optional debug msg
    # Use .get() for safer access in case a key is missing, providing a fallback if needed
    db_url = DEFAULT_CONFIG.get(DB_URL_KEY, "fallback_test_db_url_if_needed")
    some_key = DEFAULT_CONFIG.get(API_KEY_KEY)

# Use the determined config values (db_url, some_key) in your API logic
print(f"Using Database URL: {db_url}")
print(f"Using API Key: {some_key}")
# --- / Configuration Fetching Logic ---

```

**Guidance:**

* Apply this pattern for any configuration that might differ between test and live environments (database connections, external API keys, feature flags, etc.).
* Ensure `DEFAULT_CONFIG` in your `core.py` is defined with appropriate *test* or safe default values.
* Remember to `import os`.
* Use the actual `get_config` function provided by the LitePolis environment when running live (not under test). Ensure you use your actual package name (from `pyproject.toml`) as the first argument to `get_config`.