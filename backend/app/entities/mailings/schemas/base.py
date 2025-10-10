from entities.mailings.enums.statuses import MailingStatus
from pydantic import BaseModel


class MailingBaseSchema(BaseModel):
    status: MailingStatus
