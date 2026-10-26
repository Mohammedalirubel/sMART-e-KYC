"""Future integration boundaries. No live services are configured or invoked."""
from dataclasses import dataclass
from typing import Optional

@dataclass
class VerificationResult:
    status: str  # DEMO_ONLY, VERIFIED, FAILED, PENDING
    reference: Optional[str] = None
    score: Optional[float] = None

class NIDGateway:
    def verify(self, nid: str, dob: str, front: bytes, back: bytes) -> VerificationResult:
        raise NotImplementedError('Requires bank-approved NID API and credentials')

class BiometricGateway:
    def verify_liveness_and_face(self, selfie: bytes, reference_id: str) -> VerificationResult:
        raise NotImplementedError('Requires authorized liveness and face comparison provider')

class SMSGateway:
    def send_otp(self, phone: str, code: str) -> str:
        raise NotImplementedError('Requires SMS provider and secure server-side OTP service')

class ComplianceGateway:
    def screen_and_risk_grade(self, customer: dict) -> VerificationResult:
        raise NotImplementedError('Requires AML/sanctions/PEP integration and bank risk policy')

class CoreBankingGateway:
    def create_account(self, approved_application_id: str) -> str:
        raise NotImplementedError('Requires bank authorization, maker-checker and CBS API')
