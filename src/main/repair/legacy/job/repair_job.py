from typing import Set

from money import Money
from repair.legacy.job.common_base_abstract_job import CommonBaseAbstractJob
from repair.legacy.parts.parts import Parts


class RepairJob(CommonBaseAbstractJob):
    parts_to_repair: Set[Parts]
    estimated_value: Money
