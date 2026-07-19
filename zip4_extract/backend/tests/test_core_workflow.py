"""
Regression coverage for the workflow this project has been manually
smoke-testing since Phase 1: auth, RBAC enforcement, and the full
Lead -> Client -> Project -> Task lifecycle including the two derived-data
business rules (lead conversion, project progress auto-recalculation).
"""
from app.core.security import hash_password
from app.models.identity import Role, User


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestAuth:
    def test_login_success(self, client, founder_token):
        assert founder_token

    def test_login_wrong_password(self, client, founder_token):
        resp = client.post("/api/v1/auth/login", json={"email": "founder@test.com", "password": "wrong"})
        assert resp.status_code == 401

    def test_me_requires_token(self, client):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_me_with_token(self, client, founder_token):
        resp = client.get("/api/v1/auth/me", headers=auth_headers(founder_token))
        assert resp.status_code == 200
        assert resp.json()["email"] == "founder@test.com"


class TestRBAC:
    def test_role_with_no_permissions_is_blocked(self, client, db_session):
        role = Role(name="Guest", is_system_role=True)
        db_session.add(role)
        db_session.commit()
        db_session.refresh(role)
        user = User(email="guest@test.com", hashed_password=hash_password("Test1234!"),
                    full_name="Guest", role_id=role.id, is_active=True)
        db_session.add(user)
        db_session.commit()

        login = client.post("/api/v1/auth/login", json={"email": "guest@test.com", "password": "Test1234!"})
        token = login.json()["access_token"]

        resp = client.get("/api/v1/leads", headers=auth_headers(token))
        assert resp.status_code == 403

    def test_founder_bypasses_permission_checks(self, client, founder_token):
        resp = client.get("/api/v1/leads", headers=auth_headers(founder_token))
        assert resp.status_code == 200


class TestLeadToClientToProjectWorkflow:
    def test_full_lifecycle(self, client, founder_token, vertical_id):
        h = auth_headers(founder_token)

        # 1. Create a lead
        lead_resp = client.post("/api/v1/leads", headers=h, json={
            "vertical_id": vertical_id, "full_name": "Test Lead", "phone": "9999999999", "stage": "New",
        })
        assert lead_resp.status_code == 200
        lead = lead_resp.json()
        assert lead["is_converted"] is False

        # 2. Convert to client
        convert_resp = client.post(f"/api/v1/clients/convert-lead/{lead['id']}", headers=h)
        assert convert_resp.status_code == 201
        client_obj = convert_resp.json()
        assert client_obj["display_name"] == "Test Lead"

        # Lead should now show as converted, never deleted
        lead_check = client.get(f"/api/v1/leads/{lead['id']}", headers=h)
        assert lead_check.json()["is_converted"] is True

        # Converting the same lead twice should fail
        second_convert = client.post(f"/api/v1/clients/convert-lead/{lead['id']}", headers=h)
        assert second_convert.status_code == 400

        # Contact should have been carried over
        client_detail = client.get(f"/api/v1/clients/{client_obj['id']}", headers=h).json()
        assert len(client_detail["contacts"]) == 1
        assert client_detail["contacts"][0]["phone"] == "9999999999"

        # 3. Create a project for that client
        project_resp = client.post("/api/v1/projects", headers=h, json={
            "vertical_id": vertical_id, "client_id": client_obj["id"], "name": "Test Project",
        })
        assert project_resp.status_code == 200
        project = project_resp.json()
        assert project["progress_percent"] == 0

        # 4. Create two tasks under the project
        t1 = client.post("/api/v1/tasks", headers=h, json={"project_id": project["id"], "title": "Task 1"}).json()
        client.post("/api/v1/tasks", headers=h, json={"project_id": project["id"], "title": "Task 2"}).json()

        # 5. Mark one done -> progress should be 50%
        client.patch(f"/api/v1/tasks/{t1['id']}", headers=h, json={"status": "done"})
        project_after = client.get(f"/api/v1/projects/{project['id']}", headers=h).json()
        assert project_after["progress_percent"] == 50

    def test_subtask_relationship_direction(self, client, founder_token, vertical_id, db_session):
        """Regression test for the inverted self-referential FK bug found
        in the Phase 1/2 audit: a parent task's subtasks list must contain
        its children, not its own parent."""
        h = auth_headers(founder_token)
        project = client.post("/api/v1/projects", headers=h, json={
            "vertical_id": vertical_id, "name": "Subtask Test Project",
        }).json()
        parent = client.post("/api/v1/tasks", headers=h, json={
            "project_id": project["id"], "title": "Parent task",
        }).json()
        client.post("/api/v1/tasks", headers=h, json={
            "project_id": project["id"], "parent_task_id": parent["id"], "title": "Child task",
        })

        from app.models.project import ProjectTask
        parent_row = db_session.query(ProjectTask).filter(ProjectTask.id == parent["id"]).first()
        assert len(parent_row.subtasks) == 1
        assert parent_row.subtasks[0].title == "Child task"

    def test_project_progress_resets_when_last_task_deleted(self, client, founder_token, vertical_id):
        h = auth_headers(founder_token)
        project = client.post("/api/v1/projects", headers=h, json={
            "vertical_id": vertical_id, "name": "Progress Reset Test",
        }).json()
        task = client.post("/api/v1/tasks", headers=h, json={
            "project_id": project["id"], "title": "Only task",
        }).json()
        client.patch(f"/api/v1/tasks/{task['id']}", headers=h, json={"status": "done"})
        assert client.get(f"/api/v1/projects/{project['id']}", headers=h).json()["progress_percent"] == 100

        client.delete(f"/api/v1/tasks/{task['id']}", headers=h)
        assert client.get(f"/api/v1/projects/{project['id']}", headers=h).json()["progress_percent"] == 0
