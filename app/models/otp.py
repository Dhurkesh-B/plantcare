from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base

class OtpCode(Base):
    __tablename__ = "otps"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=False)
    username = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)
    otp_code = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
