"""
Comprehensive pytest tests for the FastAPI activities API.
Tests all endpoints with both success and error cases using the AAA pattern:
- Arrange: Set up test data and conditions
- Act: Execute the action being tested
- Assert: Verify the results
"""

import pytest


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_redirects_to_index(self, client):
        """
        Arrange: Root endpoint is defined
        Act: Make GET request to /
        Assert: Should redirect to /static/index.html with 307 status
        """
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]

    def test_root_redirect_follows(self, client):
        """
        Arrange: Root endpoint is defined
        Act: Make GET request to / with follow_redirects
        Assert: Should return 200 status code
        """
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200


class TestGetActivities:
    """Tests for the GET /activities endpoint."""

    def test_get_activities_success(self, client):
        """
        Arrange: Activities endpoint exists
        Act: Send GET request to /activities
        Assert: Should return 200 and valid dictionary of activities
        """
        response = client.get("/activities")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_get_activities_contains_expected_fields(self, client):
        """
        Arrange: Activities with known structure exist
        Act: Fetch activities from endpoint
        Assert: Each activity should contain required fields
        """
        response = client.get("/activities")
        data = response.json()

        # Check a specific activity has required fields
        activity = data.get("Chess Club")
        assert activity is not None
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity

    def test_get_activities_participants_is_list(self, client):
        """
        Arrange: Activities with participants lists exist
        Act: Fetch all activities
        Assert: Participants should be lists of strings
        """
        response = client.get("/activities")
        data = response.json()

        for activity_name, activity_data in data.items():
            assert isinstance(activity_data["participants"], list)
            for participant in activity_data["participants"]:
                assert isinstance(participant, str)

    def test_get_all_nine_activities(self, client):
        """
        Arrange: Nine activities are defined in the system
        Act: Fetch all activities from endpoint
        Assert: All 9 expected activities should be present
        """
        response = client.get("/activities")
        data = response.json()

        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Soccer Club",
            "Art Club",
            "Drama Club",
            "Debate Club",
            "Science Club"
        ]

        for activity in expected_activities:
            assert activity in data


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success(self, client, sample_email):
        """
        Arrange: Sample email for new participant
        Act: POST signup for Chess Club with new email
        Assert: Should return 200 with success message
        """
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": sample_email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert sample_email in data["message"]
        assert "Chess Club" in data["message"]
        assert "Signed up" in data["message"]

    def test_signup_adds_participant(self, client, sample_email):
        """
        Arrange: New email not yet registered for Chess Club
        Act: Signup user and fetch activities
        Assert: User should appear in Chess Club participants
        """
        # First, verify the user is not in the activity
        response = client.get("/activities")
        activities = response.json()
        assert sample_email not in activities["Chess Club"]["participants"]

        # Signup
        client.post(
            "/activities/Chess Club/signup",
            params={"email": sample_email}
        )

        # Verify the user is now in the activity
        response = client.get("/activities")
        activities = response.json()
        assert sample_email in activities["Chess Club"]["participants"]

    def test_signup_nonexistent_activity(self, client, sample_email):
        """
        Arrange: Try to signup for activity that doesn't exist
        Act: POST to signup endpoint with invalid activity
        Assert: Should return 404 with activity not found error
        """
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": sample_email}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_already_registered(self, client):
        """
        Arrange: Email already registered for Chess Club
        Act: Try to signup with existing participant email
        Assert: Should return 400 with already signed up error
        """
        # Use an email that's already registered
        existing_email = "michael@mergington.edu"

        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": existing_email}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_multiple_activities(self, client, sample_email):
        """
        Arrange: Sample email for signup to multiple activities
        Act: Signup for Chess Club then Programming Class
        Assert: User should appear in both activities
        """
        # Sign up for first activity
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": sample_email}
        )
        assert response1.status_code == 200

        # Sign up for second activity
        response2 = client.post(
            "/activities/Programming Class/signup",
            params={"email": sample_email}
        )
        assert response2.status_code == 200

        # Verify in both activities
        response = client.get("/activities")
        activities = response.json()
        assert sample_email in activities["Chess Club"]["participants"]
        assert sample_email in activities["Programming Class"]["participants"]

    def test_signup_preserves_other_participants(self, client, sample_email):
        """
        Arrange: Gym Class has existing participants
        Act: Signup new participant for Gym Class
        Assert: Existing participants should still be present
        """
        # Get original participants
        response = client.get("/activities")
        original_count = len(response.json()["Gym Class"]["participants"])

        # Sign up new participant
        client.post(
            "/activities/Gym Class/signup",
            params={"email": sample_email}
        )

        # Verify original participants are still there
        response = client.get("/activities")
        current_participants = response.json()["Gym Class"]["participants"]
        assert len(current_participants) == original_count + 1
        assert "john@mergington.edu" in current_participants
        assert "olivia@mergington.edu" in current_participants

    def test_signup_email_case_sensitive(self, client, sample_email):
        """
        Arrange: Email with specific case
        Act: Signup with that email and verify it's stored as-is
        Assert: Email should appear with original casing
        """
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": sample_email}
        )
        assert response.status_code == 200

        # Verify it was added with the exact case provided
        response = client.get("/activities")
        activities = response.json()
        assert sample_email in activities["Chess Club"]["participants"]

    def test_signup_missing_email_param(self, client):
        """
        Arrange: Signup endpoint requires email parameter
        Act: Call signup without email parameter
        Assert: Should return 422 Unprocessable Entity
        """
        response = client.post("/activities/Chess Club/signup")
        assert response.status_code == 422  # Unprocessable Entity


class TestUnregisterEndpoint:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint."""

    def test_unregister_success(self, client):
        """
        Arrange: Existing participant in Chess Club
        Act: DELETE unregister existing participant
        Assert: Should return 200 with success message
        """
        # Use an existing participant
        existing_email = "michael@mergington.edu"

        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": existing_email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert existing_email in data["message"]
        assert "Chess Club" in data["message"]
        assert "Unregistered" in data["message"]

    def test_unregister_removes_participant(self, client):
        """
        Arrange: Existing participant in Chess Club
        Act: Unregister the participant and fetch activities
        Assert: Participant should be removed from activity
        """
        existing_email = "michael@mergington.edu"

        # Verify user is in activity before unregister
        response = client.get("/activities")
        assert existing_email in response.json()["Chess Club"]["participants"]

        # Unregister
        client.delete(
            "/activities/Chess Club/unregister",
            params={"email": existing_email}
        )

        # Verify user is removed
        response = client.get("/activities")
        assert existing_email not in response.json()["Chess Club"]["participants"]

    def test_unregister_nonexistent_activity(self, client):
        """
        Arrange: Try to unregister from non-existent activity
        Act: DELETE from invalid activity
        Assert: Should return 404 with activity not found error
        """
        response = client.delete(
            "/activities/Nonexistent Activity/unregister",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_not_registered(self, client):
        """
        Arrange: Email not registered for Chess Club
        Act: Try to unregister non-participant email
        Assert: Should return 400 with not signed up error
        """
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_unregister_preserves_other_participants(self, client):
        """
        Arrange: Chess Club with multiple participants
        Act: Unregister one participant
        Assert: Other participants should remain unchanged
        """
        # Get original participants
        response = client.get("/activities")
        original = response.json()["Chess Club"]["participants"].copy()

        # Unregister one participant
        client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "michael@mergington.edu"}
        )

        # Verify other participants are still there
        response = client.get("/activities")
        current = response.json()["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in current
        assert len(current) == len(original) - 1

    def test_unregister_then_signup_again(self, client):
        """
        Arrange: Existing participant
        Act: Unregister them, then signup again
        Assert: Should successfully re-join the activity
        """
        email = "michael@mergington.edu"

        # Unregister
        client.delete(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )

        # Sign up again
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == 200

        # Verify in activity
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]

    def test_unregister_missing_email_param(self, client):
        """
        Arrange: Unregister endpoint requires email parameter
        Act: Call unregister without email parameter
        Assert: Should return 422 Unprocessable Entity
        """
        response = client.delete("/activities/Chess Club/unregister")
        assert response.status_code == 422


class TestIntegrationScenarios:
    """Integration tests for realistic user workflows and scenarios."""

    def test_full_signup_flow(self, client, sample_email):
        """
        Arrange: Fresh participant and empty signup state
        Act: View activities, signup, verify participation
        Assert: Participant count increases and user is registered
        """
        # View activities
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        initial_count = len(activities["Chess Club"]["participants"])

        # Sign up
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": sample_email}
        )
        assert response.status_code == 200

        # Verify signup
        response = client.get("/activities")
        assert sample_email in response.json()["Chess Club"]["participants"]
        assert len(response.json()["Chess Club"]["participants"]) == initial_count + 1

    def test_signup_and_unregister_flow(self, client, sample_email):
        """
        Arrange: Fresh participant
        Act: Signup for activity, then unregister
        Assert: User joins then leaves the activity
        """
        # Sign up
        response = client.post(
            "/activities/Programming Class/signup",
            params={"email": sample_email}
        )
        assert response.status_code == 200

        # Verify signup
        response = client.get("/activities")
        assert sample_email in response.json()["Programming Class"]["participants"]

        # Unregister
        response = client.delete(
            "/activities/Programming Class/unregister",
            params={"email": sample_email}
        )
        assert response.status_code == 200

        # Verify unregister
        response = client.get("/activities")
        assert sample_email not in response.json()["Programming Class"]["participants"]

    def test_multiple_users_signup(self, client):
        """
        Arrange: Multiple unique emails for signup
        Act: All signup for the same activity
        Assert: All should successfully register
        """
        emails = [
            "user1@mergington.edu",
            "user2@mergington.edu",
            "user3@mergington.edu"
        ]

        # All sign up for same activity
        for email in emails:
            response = client.post(
                "/activities/Soccer Club/signup",
                params={"email": email}
            )
            assert response.status_code == 200

        # Verify all are signed up
        response = client.get("/activities")
        participants = response.json()["Soccer Club"]["participants"]
        for email in emails:
            assert email in participants