from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "assistant_supervision" / "remote_helper.ps1"


class R346AssistantPartialWebRepairContract(unittest.TestCase):
    def test_partial_web_is_repaired_without_stopping_workers(self):
        text = HELPER.read_text(encoding="utf-8-sig")
        marker = "EZS_ASSISTANT_WEB_PARTIAL_REPAIR_READY"
        self.assertIn(marker, text)

        block = text.split(
            "# Repair a recognized partial Web instance without stopping distributed/profile",
            1,
        )[1].split("$webEncoded = New-WebEncodedCommand", 1)[0]

        self.assertIn("$webHas8712 -xor $webHas8713", block)
        self.assertIn("& $webStopPath", block)
        self.assertNotIn("Remove-TaskExact -TaskName $distributedTaskName", block)
        self.assertNotIn("Remove-TaskExact -TaskName $profileTaskName", block)
        self.assertNotIn("Stop-Process", block)

    def test_web_start_follows_partial_repair(self):
        text = HELPER.read_text(encoding="utf-8-sig")
        repair = text.index("EZS_ASSISTANT_WEB_PARTIAL_REPAIR_READY")
        start = text.index("$webEncoded = New-WebEncodedCommand", repair)
        self.assertLess(repair, start)


if __name__ == "__main__":
    unittest.main()
