"""
Regression coverage for Client notes/timeline -- mirrors
test_leads_advanced.py's TestLeadNotesAndTimeline exactly.
"""


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestClientNotesAndTimeline:
    def test_notes_and_timeline_on_direct_create(self, client, founder_token):
        h = auth_headers(founder_token)
        c = client.post("/api/v1/clients", headers=h, json={"display_name": "Direct Client Co"}).json()

        # Creation itself should already be on the timeline
        timeline = client.get(f"/api/v1/clients/{c['id']}/timeline", headers=h).json()
        assert any(t["activity_type"] == "created" for t in timeline)

        client.post(f"/api/v1/clients/{c['id']}/notes", headers=h, json={"note": "Kickoff call scheduled."})
        notes = client.get(f"/api/v1/clients/{c['id']}/notes", headers=h).json()
        assert len(notes) == 1
        assert notes[0]["note"] == "Kickoff call scheduled."

        client.patch(f"/api/v1/clients/{c['id']}", headers=h, json={"status": "inactive"})
        timeline_after = client.get(f"/api/v1/clients/{c['id']}/timeline", headers=h).json()
        assert any(t["activity_type"] == "status_change" for t in timeline_after)

    def test_timeline_logs_contact_added(self, client, founder_token):
        h = auth_headers(founder_token)
        c = client.post("/api/v1/clients", headers=h, json={"display_name": "Contact Timeline Co"}).json()
        client.post(f"/api/v1/clients/{c['id']}/contacts", headers=h, json={"first_name": "Aisha", "last_name": "Khan"})
        timeline = client.get(f"/api/v1/clients/{c['id']}/timeline", headers=h).json()
        assert any(t["activity_type"] == "contact_added" for t in timeline)

    def test_timeline_logs_conversion_from_lead(self, client, founder_token, vertical_id):
        h = auth_headers(founder_token)
        lead = client.post("/api/v1/leads", headers=h, json={
            "vertical_id": vertical_id, "full_name": "Convert Timeline Lead",
        }).json()
        converted = client.post(f"/api/v1/clients/convert-lead/{lead['id']}", headers=h).json()
        timeline = client.get(f"/api/v1/clients/{converted['id']}/timeline", headers=h).json()
        activity_types = {t["activity_type"] for t in timeline}
        assert "created" in activity_types
        assert "converted_from_lead" in activity_types
