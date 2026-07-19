"""
Regression coverage for Phase 4's Lead-completion features: duplicate
detection, notes/timeline exposure, bulk update/delete, and CSV
import/export.
"""
import io


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestLeadDuplicateDetection:
    def test_duplicate_phone_is_rejected(self, client, founder_token, vertical_id):
        h = auth_headers(founder_token)
        payload = {"vertical_id": vertical_id, "full_name": "Original Lead", "phone": "5550001111"}
        first = client.post("/api/v1/leads", headers=h, json=payload)
        assert first.status_code == 200

        dup = client.post("/api/v1/leads", headers=h, json={
            "vertical_id": vertical_id, "full_name": "Different Name Same Phone", "phone": "5550001111",
        })
        assert dup.status_code == 409
        assert dup.json()["detail"]["matches"][0]["full_name"] == "Original Lead"

    def test_force_bypasses_duplicate_check(self, client, founder_token, vertical_id):
        h = auth_headers(founder_token)
        payload = {"vertical_id": vertical_id, "full_name": "Lead A", "phone": "5550002222"}
        client.post("/api/v1/leads", headers=h, json=payload)

        forced = client.post("/api/v1/leads?force=true", headers=h, json={
            "vertical_id": vertical_id, "full_name": "Lead B", "phone": "5550002222",
        })
        assert forced.status_code == 200

    def test_no_false_positive_when_both_blank(self, client, founder_token, vertical_id):
        h = auth_headers(founder_token)
        client.post("/api/v1/leads", headers=h, json={"vertical_id": vertical_id, "full_name": "No Contact Info"})
        second = client.post("/api/v1/leads", headers=h, json={"vertical_id": vertical_id, "full_name": "Also No Contact"})
        assert second.status_code == 200  # neither has phone/email, must not collide


class TestLeadNotesAndTimeline:
    def test_notes_and_timeline(self, client, founder_token, vertical_id):
        h = auth_headers(founder_token)
        lead = client.post("/api/v1/leads", headers=h, json={
            "vertical_id": vertical_id, "full_name": "Timeline Test Lead",
        }).json()

        client.post(f"/api/v1/leads/{lead['id']}/notes", headers=h, json={"note": "First contact made."})
        notes = client.get(f"/api/v1/leads/{lead['id']}/notes", headers=h).json()
        assert len(notes) == 1
        assert notes[0]["note"] == "First contact made."

        client.patch(f"/api/v1/leads/{lead['id']}", headers=h, json={"stage": "Contacted"})
        timeline = client.get(f"/api/v1/leads/{lead['id']}/timeline", headers=h).json()
        activity_types = {t["activity_type"] for t in timeline}
        assert "created" in activity_types
        assert "stage_change" in activity_types


class TestLeadBulkOperations:
    def test_bulk_update_and_delete(self, client, founder_token, vertical_id):
        h = auth_headers(founder_token)
        ids = []
        for i in range(3):
            lead = client.post("/api/v1/leads", headers=h, json={
                "vertical_id": vertical_id, "full_name": f"Bulk Lead {i}", "phone": f"666000000{i}",
            }).json()
            ids.append(lead["id"])

        bulk_update = client.patch("/api/v1/leads/bulk", headers=h, json={
            "ids": ids, "updates": {"stage": "Qualified"},
        })
        assert bulk_update.status_code == 200
        assert bulk_update.json()["affected"] == 3

        for lead_id in ids:
            assert client.get(f"/api/v1/leads/{lead_id}", headers=h).json()["stage"] == "Qualified"

        bulk_delete = client.post("/api/v1/leads/bulk-delete", headers=h, json={
            "ids": ids + ["fake-id-does-not-exist"],
        })
        assert bulk_delete.status_code == 200
        result = bulk_delete.json()
        assert result["affected"] == 3
        assert result["not_found"] == ["fake-id-does-not-exist"]

        # Deleted leads should no longer resolve
        assert client.get(f"/api/v1/leads/{ids[0]}", headers=h).status_code == 404


class TestLeadCSVImportExport:
    def test_import_then_export(self, client, founder_token, vertical_id):
        h = auth_headers(founder_token)
        csv_content = (
            "full_name,company_name,email,phone,whatsapp_number,stage,priority\n"
            "CSV Lead One,Acme Co,csvlead1@test.com,7770001111,,New,high\n"
            ",Missing Name Co,,7770001112,,New,low\n"
        )
        files = {"file": ("leads.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        resp = client.post("/api/v1/leads/import", headers=h, data={"vertical_id": vertical_id}, files=files)
        assert resp.status_code == 200
        result = resp.json()
        assert result["created"] == 1
        assert result["skipped_duplicates"] == 0
        assert len(result["errors"]) == 1

        export = client.get(f"/api/v1/leads/export?vertical_id={vertical_id}", headers=h)
        assert export.status_code == 200
        assert "CSV Lead One" in export.text
        assert "Missing Name Co" not in export.text  # the error row was never created

    def test_import_skips_existing_duplicates(self, client, founder_token, vertical_id):
        h = auth_headers(founder_token)
        client.post("/api/v1/leads", headers=h, json={
            "vertical_id": vertical_id, "full_name": "Pre-existing Lead", "phone": "8880009999",
        })
        csv_content = (
            "full_name,company_name,email,phone,whatsapp_number,stage,priority\n"
            "Duplicate Of Existing,,,8880009999,,New,medium\n"
        )
        files = {"file": ("leads.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        resp = client.post("/api/v1/leads/import", headers=h, data={"vertical_id": vertical_id}, files=files)
        result = resp.json()
        assert result["created"] == 0
        assert result["skipped_duplicates"] == 1
