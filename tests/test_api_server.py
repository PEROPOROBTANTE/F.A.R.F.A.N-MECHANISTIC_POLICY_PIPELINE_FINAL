import pytest
from saaaaaa.api.api_server import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/api/v1/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'

def test_constellation_map_endpoint(client):
    """Test the new constellation map endpoint."""
    response = client.get('/api/v1/constellation_map')
    assert response.status_code == 200
    assert response.json['status'] == 'success'
    assert 'nodes' in response.json['data']
    assert 'links' in response.json['data']
