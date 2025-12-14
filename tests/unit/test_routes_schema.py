"""
Test /v1/models endpoint schema compliance.

Verifies:
- Response structure matches OpenAI schema (object=list, data[].id)
- Virtual models (router-auto, router-local, router-code) are present
"""


class TestModelsEndpoint:
    """Tests for /v1/models OpenAI-compatible endpoint."""

    def test_models_response_structure(self, client, auth_headers):
        """/v1/models should return OpenAI-compatible structure."""
        response = client.get("/v1/models", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("object") == "list", "Response must have object=list"
        assert "data" in data, "Response must have data array"
        assert isinstance(data["data"], list), "data must be a list"
        
        # Each model entry must have required fields
        for model in data["data"]:
            assert "id" in model, "Each model must have an id"
            assert "object" in model, "Each model must have object=model"
            assert model["object"] == "model"

    def test_virtual_models_present(self, client, auth_headers):
        """/v1/models should include virtual router models."""
        response = client.get("/v1/models", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        model_ids = {m.get("id") for m in data.get("data", [])}
        
        required_virtual = {"router-auto", "router-local", "router-code"}
        missing = required_virtual - model_ids
        
        assert not missing, f"Missing virtual models: {missing}"

    def test_concrete_models_present(self, client, auth_headers):
        """/v1/models should include concrete local models."""
        response = client.get("/v1/models", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        model_ids = {m.get("id") for m in data.get("data", [])}
        
        # At minimum, local models should be present
        assert "local-chat" in model_ids, "local-chat should be in models"
        assert "local-code" in model_ids, "local-code should be in models"
