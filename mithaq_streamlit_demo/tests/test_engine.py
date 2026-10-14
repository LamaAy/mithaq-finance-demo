import unittest
from engine import DemoEngine, AGENT_ID, OPERATION

class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.e = DemoEngine()
        self.r = {"agent_id":AGENT_ID,"operation":OPERATION,"supplier":"Supplier A","amount_sar":35000,"invoice":"INV-104"}
    def test_allow_and_one_time_execution(self):
        rid, status, _ = self.e.request(self.r)
        self.assertEqual(status,"ALLOW")
        token = self.e.issue_permit(rid,self.r)
        self.assertTrue(self.e.execute(self.r,token)[0])
        self.assertFalse(self.e.execute(self.r,token)[0])
        self.assertEqual(self.e.balance,265000)
    def test_modified_transaction_blocked(self):
        rid,_,_=self.e.request(self.r)
        token=self.e.issue_permit(rid,self.r)
        altered=dict(self.r,amount_sar=90000)
        self.assertFalse(self.e.execute(altered,token)[0])
        self.assertEqual(self.e.balance,300000)
    def test_unknown_supplier_denied(self):
        self.r["supplier"]="Unknown"
        rid,status,_=self.e.request(self.r)
        self.assertEqual(status,"DENY")
        with self.assertRaises(ValueError): self.e.issue_permit(rid,self.r)
    def test_approval(self):
        self.r["amount_sar"]=75000
        rid,status,_=self.e.request(self.r)
        self.assertEqual(status,"REQUIRE_APPROVAL")
        with self.assertRaises(ValueError): self.e.issue_permit(rid,self.r)
        self.e.approve(rid,"Finance Manager (demo)")
        token=self.e.issue_permit(rid,self.r)
        self.assertTrue(self.e.execute(self.r,token)[0])
    def test_unreviewed_request_cannot_be_permitted(self):
        with self.assertRaises(ValueError): self.e.issue_permit("REQ-FAKE",self.r)
    def test_expired_delegation(self):
        rid,_,_=self.e.request(self.r)
        token=self.e.issue_permit(rid,self.r)
        self.e.delegation["expires_at"]=0
        self.assertFalse(self.e.execute(self.r,token)[0])
    def test_forged_signature(self):
        rid,_,_=self.e.request(self.r)
        token=self.e.issue_permit(rid,self.r)
        token["signature"]="bad"
        self.assertFalse(self.e.execute(self.r,token)[0])
if __name__=="__main__": unittest.main()
