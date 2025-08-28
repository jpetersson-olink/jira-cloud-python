# issues.py

class Issues(object):
    def __init__(self, client):
        self._client = client

    def _base(self):
        """
        Return a valid REST v3 base URL. If _BASE_URL and cloud_id are missing,
        auto-detect cloud_id via accessible-resources and set it.
        """
        base = getattr(self._client, "_BASE_URL", None)
        if base:
            return base

        # Prefer already-known cloud_id if present
        cloud_id = getattr(self._client, "cloud_id", None) or getattr(self._client, "_cloud_id", None)
        if not cloud_id:
            # Auto-bootstrap cloudId using the access token (no cloudId needed for this call)
            # Raises cleanly if no token or the call fails.
            resources = self._client.get_resource_list()
            if not resources:
                raise RuntimeError("No accessible Jira resources found. Are you authenticated?")
            cloud_id = resources[0].get("id")
            if not cloud_id:
                raise RuntimeError("Accessible resources returned no cloudId.")
            self._client.set_cloud_id(cloud_id)

        # Ensure _BASE_URL is computed and cached on the client
        base = "{}/{}/{}".format(self._client.BASE_URL, cloud_id, self._client.API_URL)
        self._client._BASE_URL = base
        return base

    def get_issue(self, issue_id, params=None):
        """Returns the details for an issue by ID or key."""
        return self._client._get(self._base() + 'issue/{}'.format(issue_id), params=params)

    def create_issue(self, data, params=None):
        """Creates an issue (or subtask). Expects a dict payload in 'data'."""
        return self._client._post(self._base() + 'issue', json=data, params=params)

    def delete_issue(self, issue_id, params=None):
        """Deletes an issue by ID or key."""
        return self._client._delete(self._base() + 'issue/{}'.format(issue_id), params=params)

    def get_create_issue_metadata(self, params=None):
        """Returns project/issue-type details and (optionally) create screen fields."""
        return self._client._get(self._base() + 'issue/createmeta', params=params)

    def search_for_issues_using_jql(self, data: dict):
        """
        Search issues using JQL against the new endpoint:
          GET /rest/api/3/search/jql

        Backwards compatible with prior signature that accepted a dict.
        We pass JQL and paging as query params; 'fields' is sent as a comma-separated string.
        Note: 'expand' is intentionally not sent here (use per-issue expands if needed).
        """
        url = self._base() + 'search/jql'

        # Extract values with safe defaults
        jql = data.get("jql") or "order by created desc"
        start_at = int(data.get("startAt", 0))
        max_results = int(data.get("maxResults", 50))
        fields = data.get("fields")

        # Build query params (fields must be CSV for GET)
        params = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results,
        }
        if fields:
            params["fields"] = ",".join(fields) if isinstance(fields, (list, tuple)) else str(fields)

        return self._client._get(url, params=params)
