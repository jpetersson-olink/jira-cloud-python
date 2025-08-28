# issues.py

class Issues(object):
    def __init__(self, client):
        self._client = client

    def _base(self):
        """
        Return a valid REST v3 base URL, repairing _BASE_URL from cloud_id if needed.
        Raises a clear message if neither is available.
        """
        base = getattr(self._client, "_BASE_URL", None)
        if base:
            return base

        cloud_id = getattr(self._client, "cloud_id", None) or getattr(self._client, "_cloud_id", None)
        if cloud_id:
            base = "{}/{}/{}".format(self._client.BASE_URL, cloud_id, self._client.API_URL)
            # cache it back on the client so subsequent calls are cheap
            self._client._BASE_URL = base
            return base

        raise RuntimeError("Client base URL is not set. Call client.set_cloud_id(...) after authenticating.")

    def get_issue(self, issue_id, params=None):
        """
        Returns the details for an issue by ID or key.
        """
        return self._client._get(self._base() + 'issue/{}'.format(issue_id), params=params)

    def create_issue(self, data, params=None):
        """
        Creates an issue (or subtask). Expects a dict payload in 'data'.
        """
        # Use JSON body for clarity/compat with Jira v3 REST.
        return self._client._post(self._base() + 'issue', json=data, params=params)

    def delete_issue(self, issue_id, params=None):
        """
        Deletes an issue by ID or key.
        """
        return self._client._delete(self._base() + 'issue/{}'.format(issue_id), params=params)

    def get_create_issue_metadata(self, params=None):
        """
        Returns project/issue-type details and (optionally) create screen fields.
        """
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
            if isinstance(fields, (list, tuple)):
                params["fields"] = ",".join(fields)
            else:
                params["fields"] = str(fields)

        return self._client._get(url, params=params)
